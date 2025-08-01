from datetime import datetime, timezone
from typing import Optional
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app_config import AppConfig
from data_models.workflow_models import Plan, Step, StepStatus, PlanStatus

# The name of the container we will use for our workflow state
WORKFLOW_STATE_CONTAINER = "workflow_state"

class WorkflowStateRepository:
    """Handles all database operations for Plan and Step objects in Cosmos DB."""

    def __init__(self, config: AppConfig):
        """Initializes the repository and connects to the Cosmos DB container."""
        client = CosmosClient(
            url=config.COSMOSDB_ENDPOINT, credential=config.get_azure_credential()
        )
        database = client.get_database_client(config.COSMOSDB_DATABASE)
        self.container = database.get_container_client(WORKFLOW_STATE_CONTAINER)

    async def create_plan(self, plan: Plan) -> None:
        """Saves a new plan to the database."""
        await self.container.upsert_item(body=plan.model_dump())

    async def get_plan(self, plan_id: str, tenant_id: str) -> Optional[Plan]:
        """Retrieves a single plan document using its ID and partition key (tenant_id)."""
        try:
            response = await self.container.read_item(item=plan_id, partition_key=tenant_id)
            return Plan(**response)
        except CosmosResourceNotFoundError:
            return None

    async def get_next_pending_step(self, plan_id: str, tenant_id: str) -> Optional[Step]:
        """Finds the first step in a plan that is pending."""
        plan = await self.get_plan(plan_id=plan_id, tenant_id=tenant_id)
        if not plan:
            return None
        
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                return step
        return None

    async def update_step(self, plan_id: str, tenant_id: str, updated_step: Step) -> Plan:
        """Updates a single step within a plan."""
        plan = await self.get_plan(plan_id=plan_id, tenant_id=tenant_id)
        if not plan:
            raise ValueError(f"Plan with ID '{plan_id}' not found.")

        for i, step in enumerate(plan.steps):
            if step.id == updated_step.id:
                plan.steps[i] = updated_step
                break
        else:
            raise ValueError(f"Step with ID '{updated_step.id}' not found in plan.")
        
        plan.updated_at = datetime.now(timezone.utc)
        response = await self.container.replace_item(item=plan.id, body=plan.model_dump())
        return Plan(**response)
        
    async def update_plan_status(self, plan_id: str, tenant_id: str, new_status: PlanStatus) -> Plan:
        """Updates the overall status of a plan."""
        plan = await self.get_plan(plan_id=plan_id, tenant_id=tenant_id)
        if not plan:
            raise ValueError(f"Plan with ID '{plan_id}' not found.")

        plan.status = new_status
        plan.updated_at = datetime.now(timezone.utc)
        
        response = await self.container.replace_item(item=plan.id, body=plan.model_dump())
        return Plan(**response)