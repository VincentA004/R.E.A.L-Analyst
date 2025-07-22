import logging
from abc import abstractmethod
from typing import (Any, List, Mapping, Optional)

from app_config import config
from agentic_context.cosmos_memory_kernel import CosmosMemoryContext
from data_models.messages_kernel import (ActionRequest, ActionResponse, AgentMessage, Step, StepStatus)
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.functions import KernelFunction


class BaseAgent(AzureAIAgent):
    """
    BaseAgent for R.E.A.L.-Analyst, inheriting from AzureAIAgent.
    This class provides the core logic for handling stateful, plan-based action requests.
    """

    def __init__(
        self,
        agent_name: str,
        session_id: str,
        user_id: str,
        memory_store: CosmosMemoryContext,
        tools: Optional[List[KernelFunction]] = None,
        system_message: Optional[str] = None,
        client=None, # The AIProjectClient
        definition=None, # The agent definition from Azure
    ):
        system_message = system_message or self.default_system_message(agent_name)
        
        # This is the core connection to the Azure AI Agent Service
        super().__init__(
            plugins=tools or [],
            agent_name=agent_name,
            system_prompt=system_message,
            client=client,
            definition=definition,
            # These are now managed by the client/definition objects
            deployment_name=None, 
            endpoint=None,
            api_version=None,
        )

        # Store instance variables
        self._agent_name = agent_name
        self._session_id = session_id
        self._user_id = user_id
        self._memory_store = memory_store
        self.name = agent_name # Crucial for compatibility

    @staticmethod
    def default_system_message(agent_name=None) -> str:
        return f"You are an AI assistant named {agent_name} for the R.E.A.L.-Analyst platform."

    async def handle_action_request(self, action_request: ActionRequest) -> str:
        """
        Handles a specific step from a plan by invoking the agent and persisting the state.
        """
        logging.info(f"Agent '{self._agent_name}' is handling action request for step '{action_request.step_id}'")
        step: Step = await self._memory_store.get_step(action_request.step_id, action_request.session_id)

        if not step:
            response = ActionResponse(step_id=action_request.step_id, status=StepStatus.failed, message="Step not found.")
            return response.json()

        try:
            # The agent's `invoke` method from the parent AzureAIAgent class will handle tool calls
            async_generator = self.invoke(messages=step.action)
            response_content = ""
            async for chunk in async_generator:
                if chunk is not None:
                    response_content += str(chunk)

            logging.info(f"Agent '{self._agent_name}' produced response: {response_content}")
            
            # Save the agent's response as a message in our history
            await self._memory_store.add_item(
                AgentMessage(
                    session_id=action_request.session_id, user_id=self._user_id, plan_id=action_request.plan_id,
                    content=response_content, source=self._agent_name, step_id=action_request.step_id
                )
            )
            
            # Update the step in Cosmos DB to mark it as complete
            step.status = StepStatus.completed
            step.agent_reply = response_content
            await self._memory_store.update_step(step)
            
            response = ActionResponse(
                step_id=step.id, plan_id=step.plan_id, session_id=action_request.session_id,
                result=response_content, status=StepStatus.completed
            )
            return response.json()

        except Exception as e:
            logging.exception(f"Error during agent execution for step '{step.id}': {e}")
            step.status = StepStatus.failed
            step.agent_reply = f"Error: {str(e)}"
            await self._memory_store.update_step(step)
            
            response = ActionResponse(
                step_id=action_request.step_id, plan_id=action_request.plan_id, session_id=action_request.session_id,
                result=f"Error: {str(e)}", status=StepStatus.failed
            )
            return response.json()

    @classmethod
    @abstractmethod
    async def create(cls, **kwargs) -> "BaseAgent":
        """Asynchronous factory method for creating an agent instance."""
        pass

    @staticmethod
    async def _create_azure_ai_agent_definition(agent_name: str, instructions: str, client=None, **kwargs):
        """
        Creates or retrieves an agent definition from the Azure AI Agent Service.
        """
        if client is None:
            client = config.get_ai_project_client()
        
        try:
             # This logic attempts to find an existing agent to avoid duplicates
            async for agent in client.agents.list():
                if agent.name == agent_name:
                    logging.info(f"Found existing agent definition for '{agent_name}'.")
                    return await client.agents.get(name=agent_name)
        except Exception as e:
            logging.warning(f"Could not list existing agents, proceeding to create. Error: {e}")

        logging.info(f"Creating new agent definition for '{agent_name}'...")
        return await client.agents.create_or_update(
            agent_name=agent_name,
            instructions=instructions,
            model_deployment_name=config.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME,
            **kwargs
        )