from typing import Any, Dict

from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import AgentType

class ValuationAgent(BaseAgent):
    """An agent specializing in real estate property valuation."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "ValuationAgent":
        """Asynchronous factory method to create the ValuationAgent."""
        agent_name = kwargs.get("agent_name", AgentType.VALUATION.value)
        system_message = kwargs.get("system_message", cls.default_system_message())
        
        agent_definition = await cls._create_azure_ai_agent_definition(
            agent_name=agent_name,
            instructions=system_message,
            client=kwargs.get("client")
        )
        return cls(definition=agent_definition, **kwargs)

    @staticmethod
    def default_system_message() -> str:
        return (
            "You are an expert real estate appraiser. Your sole focus is determining property value. "
            "You will be given property details and must use your tools to find comparable sales (comps), "
            "assess the property's current market value, and estimate its After-Repair Value (ARV) if applicable. "
            "Do not answer questions about zoning, investment strategy, or anything outside of property valuation."
        )