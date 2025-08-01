import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# --- Enums for Status and Naming ---

class PlanStatus(str, Enum):
    """Represents the overall status of a plan."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class StepStatus(str, Enum):
    """Represents the status of an individual step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentName(str, Enum):
    """Defines the names of our specialized agents."""
    PLANNER = "PlannerAgent"
    ZONING = "ZoningAgent"
    VALUATION = "ValuationAgent"
    INVESTMENT = "InvestmentAgent"


# --- Core Workflow Models ---

class Step(BaseModel):
    """Represents a single task within a Plan."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_name: AgentName
    action: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

class Plan(BaseModel):
    """Represents the complete, multi-step workflow for an analysis."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: str
    session_id: str
    user_id: str
    initial_request: str
    status: PlanStatus = PlanStatus.IN_PROGRESS
    steps: List[Step] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))