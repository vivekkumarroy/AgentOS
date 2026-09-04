from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    REPLANNING = "REPLANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PlanStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class FailureCategory(str, Enum):
    TOOL_ERROR = "TOOL_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    EMPTY_RESULT = "EMPTY_RESULT"
    INVALID_RESULT = "INVALID_RESULT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class VerificationResult(BaseModel):
    success: bool
    reason: str
    evidence: Optional[Dict[str, Any]] = None

class FailureDiagnosis(BaseModel):
    failure_type: FailureCategory
    reason: str
    affected_task_id: str
    recoverable: bool
    suggested_recovery: str

class RecoveryPlan(BaseModel):
    original_task_id: str
    strategy: str
    revised_task_description: str
    retry_allowed: bool

class Task(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task.")
    description: str = Field(..., description="A detailed description of what needs to be done.")
    dependencies: List[str] = Field(default_factory=list, description="List of task_ids that must be completed before this task.")
    required_tools: List[str] = Field(default_factory=list, description="Tools required for this task (e.g. 'web_search', 'python').")
    expected_output: str = Field(..., description="What the task should produce on success.")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    
    # Phase 3 additions
    retry_count: int = 0
    max_retries: int = 3
    verification_result: Optional[VerificationResult] = None
    diagnosis: Optional[FailureDiagnosis] = None
    recovery_plan: Optional[RecoveryPlan] = None

class Plan(BaseModel):
    goal: str = Field(..., description="The high-level user goal this plan addresses.")
    tasks: List[Task] = Field(..., description="The tasks that make up the plan.")
    status: PlanStatus = Field(default=PlanStatus.IN_PROGRESS)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Observation(BaseModel):
    result: str
    status: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentExecutionStatus(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class AgentState(BaseModel):
    user_goal: str
    current_plan: Optional[Plan] = None
    tasks_state: Dict[str, Task] = Field(default_factory=dict)
    observations: List[Observation] = Field(default_factory=list)
    status: AgentExecutionStatus = AgentExecutionStatus.IDLE
    execution_context: Dict[str, Any] = Field(default_factory=dict)
    action_history: List[ToolCall] = Field(default_factory=list)
