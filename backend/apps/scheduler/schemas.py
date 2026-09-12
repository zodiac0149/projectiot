from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TimeSlot(BaseModel):
    """Represents a precomputed free continuous time window (UTC)."""
    start_time: datetime = Field(..., description="ISO-8601 start timestamp")
    end_time: datetime = Field(..., description="ISO-8601 end timestamp")
    duration_minutes: int = Field(..., description="Available duration in minutes")

class TaskContext(BaseModel):
    """Normalized task model representation for LLM and Heuristic algorithms."""
    id: str = Field(..., description="UUID of the task")
    title: str = Field(..., description="Title of the task")
    priority: int = Field(..., ge=1, le=5, description="Priority level 1-5")
    estimated_minutes: int = Field(..., gt=0, description="Estimated duration in minutes")
    deadline: datetime = Field(..., description="Hard deadline timestamp")
    cognitive_load: str = Field(..., description="HIGH, MEDIUM, or LOW")

class AllocatedSession(BaseModel):
    task_id: str = Field(..., description="UUID of the assigned task")
    start_time: datetime = Field(..., description="ISO-8601 start timestamp")
    end_time: datetime = Field(..., description="ISO-8601 end timestamp")
    rationale: str = Field(..., description="Short explanation for this placement")

class ReschedulePlan(BaseModel):
    sessions: List[AllocatedSession]
    unplaced_task_ids: List[str] = Field(
        default_factory=list,
        description="Tasks that could not fit before deadline"
    )

class RescheduleRequest(BaseModel):
    disruption_context: str = Field(
        default="Standard autonomous schedule calculation",
        description="Context explaining the reason for reshuffling"
    )
    window_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days forward to calculate schedule"
    )
