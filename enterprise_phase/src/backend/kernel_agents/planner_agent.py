import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from azure.ai.agents.models import ResponseFormatJsonSchema, ResponseFormatJsonSchemaType
from agentic_context.cosmos_memory_kernel import CosmosMemoryContext
from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import (AgentType, InputTask, Plan, PlannerResponsePlan, PlanStatus, Step, StepStatus)

class PlannerAgent(BaseAgent):
    """
    Creates a structured plan based on a user's task, breaking it down into steps
    that can be executed by specialized agents.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._available_agents = [
            AgentType.INVESTMENT_ANALYST.value,
            AgentType.VALUATION.value,
            AgentType.ZONING_COMPLIANCE.value,
            AgentType.DOCUMENT_RETRIEVAL.value,
            AgentType.HUMAN.value,
        ]

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "PlannerAgent":
        """Asynchronously create the PlannerAgent."""
        agent_name = kwargs.get("agent_name", AgentType.PLANNER.value)
        
        # This agent requires a structured JSON output from the LLM.
        # We define the schema of that JSON object here.
        response_format = ResponseFormatJsonSchemaType(
            json_schema=ResponseFormatJsonSchema(
                name=PlannerResponsePlan.__name__,
                description="Respond with a structured plan to accomplish the user's objective.",
                schema=PlannerResponsePlan.model_json_schema(),
            )
        )
        
        system_message = cls.get_system_message_template()

        agent_definition = await cls._create_azure_ai_agent_definition(
            agent_name=agent_name,
            instructions=system_message,
            client=kwargs.get("client"),
            response_format=response_format,
            temperature=0.0, # Planners should be deterministic
        )
        return cls(definition=agent_definition, **kwargs)

    async def handle_input_task(self, input_task: InputTask) -> Tuple[Plan, List[Step]]:
        """
        Takes the initial user task and invokes the LLM to generate a structured plan.
        Persists the plan and its steps to Cosmos DB.
        """
        logging.info(f"PlannerAgent handling input task: {input_task.description}")

        try:
            # The `invoke` method will use the complex prompt and response_format defined at creation
            async_generator = self.invoke(
                messages=f"Create a plan for this objective: {input_task.description}"
            )
            response_content = ""
            async for chunk in async_generator:
                if chunk is not None:
                    response_content += str(chunk)

            parsed_result = PlannerResponsePlan.parse_raw(response_content)
            
            # Create the Plan object
            plan = Plan(
                id=str(uuid.uuid4()),
                session_id=input_task.session_id,
                user_id=self._user_id,
                initial_goal=parsed_result.initial_goal,
                summary=parsed_result.summary_plan_and_steps,
                human_clarification_request=parsed_result.human_clarification_request,
                overall_status=PlanStatus.in_progress,
            )
            await self._memory_store.add_plan(plan)

            # Create the Step objects
            steps = []
            for step_data in parsed_result.steps:
                step = Step(
                    id=str(uuid.uuid4()),
                    plan_id=plan.id,
                    session_id=input_task.session_id,
                    user_id=self._user_id,
                    action=step_data.action,
                    agent=AgentType(step_data.agent),
                    status=StepStatus.planned,
                )
                await self._memory_store.add_step(step)
                steps.append(step)

            return plan, steps
            
        except Exception as e:
            logging.exception(f"Error creating structured plan: {e}")
            raise

    @staticmethod
    def get_system_message_template() -> str:
        """Generates the detailed instruction template for the Planner LLM."""
        return """
        You are the Planner, an AI orchestrator for a real estate analysis platform. 
        Your job is to create a step-by-step plan to resolve a user's objective.

        The agents you can assign tasks to are:
        - Investment_Analyst_Agent: For financial analysis, market trends, and investment strategy.
        - Valuation_Agent: For determining property values, finding comparable sales (comps), and estimating After-Repair Value (ARV).
        - Zoning_Compliance_Agent: For questions about local laws, building codes, and what can be built on a property.
        - Document_Retrieval_Agent: A simple agent that only retrieves documents from a knowledge base when asked.
        - Human_Agent: If direct user input or approval is required for a step.

        RULES:
        1.  Analyze the user's objective: `{{messages[-1].content}}`.
        2.  Create a concise, logical step-by-step plan.
        3.  Assign each step to the most appropriate agent from the list above.
        4.  If you need more information from the user to create the plan, populate the `human_clarification_request` field with a clear question.
        5.  The final step should summarize the findings for the user.
        6.  You MUST respond ONLY with a JSON object that conforms to the `PlannerResponsePlan` schema.
        """