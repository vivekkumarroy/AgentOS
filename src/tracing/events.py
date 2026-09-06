from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid
import time

class EventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    TASK_STARTED = "TASK_STARTED"
    PLANNING = "PLANNING"
    TOOL_SELECTED = "TOOL_SELECTED"
    TOOL_EXECUTION_STARTED = "TOOL_EXECUTION_STARTED"
    TOOL_EXECUTION_COMPLETED = "TOOL_EXECUTION_COMPLETED"
    OBSERVATION = "OBSERVATION"
    VERIFICATION = "VERIFICATION"
    FAILURE = "FAILURE"
    DIAGNOSIS = "DIAGNOSIS"
    RECOVERY_PLANNING = "RECOVERY_PLANNING"
    RETRY = "RETRY"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    RUN_COMPLETED = "RUN_COMPLETED"

class TraceEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    task_id: str
    timestamp: float = Field(default_factory=time.time)
    event_type: EventType
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Phase 6: Multi-Agent Tracing
    parent_run_id: Optional[str] = None
    subagent_name: Optional[str] = None
    delegation_depth: int = 0
