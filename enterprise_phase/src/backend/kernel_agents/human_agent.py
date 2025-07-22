import logging
from typing import Any, Dict

from kernel_agents.agent_base import BaseAgent
from data_models.messages_kernel import AgentType, HumanClarification, HumanFeedback, StepStatus

class HumanAgent(BaseAgent):
    """Represents the human user for feedback and clarification."""

    def __init__(self, **kwargs: Any):
        # Human agent does not need a definition or client
        kwargs.pop("definition", None)
        kwargs.pop("client", None)
        super().__init__(**kwargs)

    @classmethod
    async def create(cls, **kwargs: Dict[str, Any]) -> "HumanAgent":
        # No Azure AI Agent definition needed for the human agent
        logging.info("Creating HumanAgent instance.")
        return cls(**kwargs)

    async def handle_action_request(self, action_request):
        # The human agent is never invoked by the system to perform an action.
        raise NotImplementedError("HumanAgent cannot handle action requests.")
        
    async def handle_human_clarification(self, clarification: HumanClarification) -> str:
        """Updates the plan in Cosmos DB with the user's clarification."""
        logging.info(f"HumanAgent handling clarification for plan {clarification.plan_id}")
        plan = await self._memory_store.get_plan(clarification.plan_id)
        if not plan:
            return f"Error: Plan {clarification.plan_id} not found."
        
        plan.human_clarification_response = clarification.human_clarification
        await self._memory_store.update_plan(plan)
        return "Clarification successfully recorded."
        
    async def handle_human_feedback(self, feedback: HumanFeedback) -> str:
        """Updates a step in Cosmos DB with the user's approval/rejection."""
        logging.info(f"HumanAgent handling feedback for step {feedback.step_id}")
        step = await self._memory_store.get_step(feedback.step_id, feedback.session_id)
        if not step:
            return f"Error: Step {feedback.step_id} not found."

        step.status = StepStatus.approved if feedback.approved else StepStatus.rejected
        step.human_feedback = feedback.human_feedback
        await self._memory_store.update_step(step)
        return f"Step {step.id} has been updated to '{step.status.value}'."

    @staticmethod
    def default_system_message() -> str:
        return "I am a proxy for the human user."