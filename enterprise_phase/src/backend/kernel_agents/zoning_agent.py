from typing import Any, Dict

from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import AgentType

class ZoningComplianceAgent(BaseAgent):
    """An agent specializing in zoning laws and building regulations."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "ZoningComplianceAgent":
        """Asynchronous factory method to create the ZoningComplianceAgent."""
        agent_name = kwargs.get("agent_name", AgentType.ZONING_COMPLIANCE.value)
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
            "You are an expert in municipal zoning laws, building codes, and local real estate regulations. "
            "Your job is to answer specific questions about what is legally permissible for a given property. "
            "You MUST use your document retrieval tools to find factual information from official zoning documents. "
            "Answer questions like 'Can I build an ADU here?', 'Is this property zoned for short-term rentals?', and 'What are the setback requirements?'. "
            "Do not provide opinions on property value or investment quality."
        )