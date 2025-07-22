# In src/backend/kernel_agents/investment_analyst_agent.py

import logging
from typing import Dict, List, Optional

from agentic_context.cosmos_memory_kernel import CosmosMemoryContext
from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import AgentType
from semantic_kernel.functions import KernelFunction

class InvestmentAnalystAgent(BaseAgent):
    """
    An agent specializing in real estate investment analysis.
    """

    # The __init__ is now much simpler, just passing args to the parent.
    def __init__(
        self,
        session_id: str,
        user_id: str,
        memory_store: CosmosMemoryContext,
        tools: Optional[List[KernelFunction]] = None,
        system_message: Optional[str] = None,
        agent_name: str = AgentType.INVESTMENT_ANALYST.value,
        client=None,
        definition=None,
    ):
        super().__init__(
            agent_name=agent_name,
            session_id=session_id,
            user_id=user_id,
            memory_store=memory_store,
            tools=tools,
            system_message=system_message or self.default_system_message(),
            client=client,
            definition=definition,
        )

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "InvestmentAnalystAgent":
        """
        Asynchronous factory method to create the InvestmentAnalystAgent.
        This is now the required pattern for instantiation.
        """
        system_message = kwargs.get("system_message", cls.default_system_message())
        agent_name = kwargs.get("agent_name", AgentType.INVESTMENT_ANALYST.value)
        
        # This creates the persistent agent definition in Azure AI Agent Service
        agent_definition = await cls._create_azure_ai_agent_definition(
            agent_name=agent_name,
            instructions=system_message,
            client=kwargs.get("client")
        )

        # Return a new instance of the class
        return cls(definition=agent_definition, **kwargs)

    @staticmethod
    def default_system_message() -> str:
        return (
            "You are an expert real estate investment analyst..." # Same prompt as before
        )