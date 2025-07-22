import logging
from typing import Type, Dict, Any, Optional

from data_models.messages_kernel import AgentType
from agentic_context.cosmos_memory_kernel import CosmosMemoryContext

# Import our new R.E.A.L.-Analyst agents
from kernel_agents.agent_base import BaseAgent
from kernel_agents.planner_agent import PlannerAgent
from kernel_agents.investment_agent import InvestmentAnalystAgent
from kernel_agents.valuation_agent import ValuationAgent
from kernel_agents.zoning_agent import ZoningComplianceAgent
from kernel_agents.document_retrieval_agent import DocumentRetrievalAgent
# We will create a HumanAgent file later
# from kernel_agents.human_agent import HumanAgent 

class AgentFactory:
    """Factory for creating R.E.A.L.-Analyst agent instances."""

    _agent_classes: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.PLANNER: PlannerAgent,
        AgentType.INVESTMENT_ANALYST: InvestmentAnalystAgent,
        AgentType.VALUATION: ValuationAgent,
        AgentType.ZONING_COMPLIANCE: ZoningComplianceAgent,
        AgentType.DOCUMENT_RETRIEVAL: DocumentRetrievalAgent,
        # AgentType.HUMAN: HumanAgent,
    }

    _agent_cache: Dict[str, Dict[AgentType, BaseAgent]] = {}

    @classmethod
    async def create_agent(
        cls,
        agent_type: AgentType,
        session_id: str,
        user_id: str,
        **kwargs: Any,
    ) -> BaseAgent:
        
        # Return from cache if instance already exists for this session
        if session_id in cls._agent_cache and agent_type in cls._agent_cache[session_id]:
            return cls._agent_cache[session_id][agent_type]

        agent_class = cls._agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Ensure memory store is created
        memory_store = kwargs.get("memory_store") or CosmosMemoryContext(session_id, user_id)
        
        # Prepare arguments for the agent's create method
        create_kwargs = {
            "session_id": session_id,
            "user_id": user_id,
            "memory_store": memory_store,
            "agent_name": agent_type.value,
            **kwargs,
        }

        # Use the new required 'create' pattern
        agent = await agent_class.create(**create_kwargs)

        # Cache the newly created agent
        if session_id not in cls._agent_cache:
            cls._agent_cache[session_id] = {}
        cls._agent_cache[session_id][agent_type] = agent
        
        return agent