from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TestCase(BaseModel):
    __test__ = False
    case_id: str
    user_goal: str
    expected_result: Optional[str] = None
    expected_tools: Optional[List[str]] = None
    success_criteria: Optional[Dict[str, Any]] = None

class EvalResult(BaseModel):
    case_id: str
    passed: bool
    failure_reason: Optional[str] = None
    duration: float
    tool_usage_count: int
    recovery_attempts: int
    final_task_status: str

class EvalReport(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    success_rate: float
    total_duration: float
    average_duration: float
    total_tool_calls: int
    total_recovery_attempts: int
    results: List[EvalResult]
