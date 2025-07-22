from typing import Any, Dict

from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import AgentType

class DocumentRetrievalAgent(BaseAgent):
    """A specialized agent for retrieving information from a vectorized knowledge base (RAG)."""

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "DocumentRetrievalAgent":
        """Asynchronous factory method to create the DocumentRetrievalAgent."""
        agent_name = kwargs.get("agent_name", AgentType.DOCUMENT_RETRIEVAL.value)
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
            "You are a document retrieval expert. Your only function is to use the provided search and retrieval tools when asked by another agent. "
            "You must execute the requested tool call with the exact parameters you are given. "
            "Do not interpret, analyze, or summarize the results. Return only the direct, raw output from the tool."
        )