import logging
from typing import Any, Dict, List, Optional

from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import (
    ActionRequest,
    AgentMessage,
    AgentType,
    HumanFeedback,
    Plan,
    Step,
    StepStatus,
)

class GroupChatManager(BaseAgent):
    """
    Acts as a Plan Executor, not a free-form chat manager.
    This agent orchestrates the execution of a structured plan created by the PlannerAgent.
    It iterates through steps, dispatches tasks to specialist agents, and waits for completion.
    """

    def __init__(self, agent_instances: Dict[str, BaseAgent], **kwargs: Any):
        # The executor itself does not have an Azure AI definition; it's a pure orchestrator.
        kwargs.pop("definition", None)
        kwargs.pop("client", None)
        super().__init__(**kwargs)
        
        self._agent_instances = agent_instances
        logging.info(f"GroupChatManager initialized with agents: {list(self._agent_instances.keys())}")

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "GroupChatManager":
        """Asynchronously create the GroupChatManager."""
        # This agent does not need an Azure AI definition, so we don't call _create_...
        return cls(**kwargs)

    async def start_plan_execution(self, plan: Plan):
        """
        Starts the execution of the entire plan. This is the entry point for the executor.
        """
        logging.info(f"Starting execution for plan '{plan.id}'.")
        await self._memory_store.add_item(
            AgentMessage(
                session_id=plan.session_id, user_id=self._user_id, plan_id=plan.id,
                content=f"I have created a plan with {len(plan.steps)} steps. I will now begin execution.",
                source=AgentType.GROUP_CHAT_MANAGER.value
            )
        )
        await self._run_execution_loop(plan.id)

    async def handle_human_feedback(self, feedback: HumanFeedback):
        """
        Handles feedback from the HumanAgent and continues the plan execution if a step was approved.
        """
        logging.info(f"Executor received human feedback for step '{feedback.step_id}'. Approved: {feedback.approved}")
        
        # The HumanAgent already updated the step status in Cosmos DB.
        # We just need to decide whether to continue the plan.
        if feedback.approved:
            logging.info(f"Step approved. Continuing plan execution for plan '{feedback.plan_id}'.")
            await self._run_execution_loop(feedback.plan_id)
        else:
            logging.warning(f"Step '{feedback.step_id}' was rejected by the user. Halting execution of plan '{feedback.plan_id}'.")
            plan = await self._memory_store.get_plan(feedback.plan_id)
            plan.status = "failed" # You might want a more specific status
            await self._memory_store.update_plan(plan)
            await self._memory_store.add_item(
                AgentMessage(
                    session_id=plan.session_id, user_id=self._user_id, plan_id=plan.id,
                    content=f"Execution halted because a step was rejected by the user.",
                    source=AgentType.GROUP_CHAT_MANAGER.value
                )
            )

    async def _run_execution_loop(self, plan_id: str):
        """
        The main loop that finds the next step and executes it.
        """
        steps = await self._memory_store.get_steps_by_plan(plan_id)
        
        # Find the next step that is ready to be executed
        next_step = self._find_next_step(steps)

        if not next_step:
            logging.info(f"No more executable steps. Plan '{plan_id}' is complete.")
            plan = await self._memory_store.get_plan(plan_id)
            plan.status = "completed"
            await self._memory_store.update_plan(plan)
            await self._memory_store.add_item(
                AgentMessage(
                    session_id=plan.session_id, user_id=self._user_id, plan_id=plan.id,
                    content="All steps have been completed successfully.",
                    source=AgentType.GROUP_CHAT_MANAGER.value
                )
            )
            return

        logging.info(f"Executing next step '{next_step.id}' for agent '{next_step.agent.value}'.")
        await self._execute_step(next_step)

    def _find_next_step(self, steps: List[Step]) -> Optional[Step]:
        """Finds the first step in the list that has a 'planned' or 'approved' status."""
        # This is a simple sequential executor. More complex logic could handle parallel steps.
        for step in sorted(steps, key=lambda s: s.timestamp): # Ensure order
            if step.status in [StepStatus.planned, StepStatus.approved]:
                return step
        return None

    async def _execute_step(self, step: Step):
        """Dispatches a single step to the appropriate agent."""
        if step.agent == AgentType.HUMAN:
            logging.info(f"Step '{step.id}' requires human input. Pausing execution.")
            # The frontend will now wait for the user to interact.
            # The `handle_human_feedback` method will be called when the user responds.
            await self._memory_store.add_item(
                AgentMessage(
                    session_id=step.session_id, user_id=self._user_id, plan_id=step.plan_id,
                    content=f"Waiting for your feedback on the following step: {step.action}",
                    source=AgentType.GROUP_CHAT_MANAGER.value,
                    step_id=step.id
                )
            )
            return

        # Find the specialist agent instance
        specialist_agent = self._agent_instances.get(step.agent.value)
        if not specialist_agent:
            logging.error(f"Executor could not find an instance for agent '{step.agent.value}'. Halting.")
            return

        # Update step status to show it's in progress
        step.status = StepStatus.in_progress
        await self._memory_store.update_step(step)
        
        # Create the formal request and dispatch it
        action_request = ActionRequest(
            step_id=step.id,
            plan_id=step.plan_id,
            session_id=step.session_id,
            action=step.action,
            agent=step.agent,
        )
        
        # The agent's `handle_action_request` will execute the step and update its status in Cosmos DB.
        await specialist_agent.handle_action_request(action_request)
        
        # After the agent is done, continue the loop to find the next step
        await self._run_execution_loop(step.plan_id)

    @staticmethod
    def default_system_message() -> str:
        return "I am the Group Chat Manager, responsible for executing plans."