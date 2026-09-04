import sys
from src.evaluation.models import TestCase
from src.evaluation.framework import Evaluator
from src.tracing.tracer import LocalTracer
from src.models.state import Plan, Task, TaskStatus, Observation, ToolCall, FailureDiagnosis, FailureCategory, RecoveryPlan
from src.verification.verifier import VerificationResult
import logging

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

class MockPlanner:
    def create_plan(self, goal):
        return Plan(goal=goal, tasks=[Task(task_id="t3", description="Recover task", expected_output="ok", status=TaskStatus.PENDING)])
    def generate_tool_call(self, task, schemas):
        if task.retry_count == 0:
            return ToolCall(tool_name="failing_tool", arguments={})
        else:
            return ToolCall(tool_name="write_file", arguments={"path": "recovered.txt", "content": "Fixed"})

class DummyRegistry:
    def get_all_schemas(self): return []

class MockExecutor:
    def __init__(self): self.registry = DummyRegistry()
    def execute_tool(self, call: ToolCall):
        if call.tool_name == "write_file": return Observation(result="File written", status="SUCCESS")
        return Observation(result="Tool failed", status="ERROR")
            
class MockVerifier:
    def verify(self, task, tool_call, obs):
        if obs.status == "SUCCESS": return VerificationResult(success=True, reason="Looks good")
        return VerificationResult(success=False, reason="Tool error")

class MockDiagnoser:
    def diagnose(self, task, obs, verif):
        return FailureDiagnosis(failure_type=FailureCategory.TOOL_ERROR, reason="Tool failed", affected_task_id=task.task_id, recoverable=True, suggested_recovery="Try another tool")

class MockReplanner:
    def create_recovery_plan(self, task, diag):
        return RecoveryPlan(original_task_id=task.task_id, strategy="Retry", revised_task_description="Try writing file", retry_allowed=True)

tracer = LocalTracer("./data/test_trace.jsonl")
evaluator = Evaluator(MockPlanner(), MockExecutor(), MockVerifier(), MockDiagnoser(), MockReplanner(), None, tracer)

report = evaluator.evaluate([TestCase(case_id="c1", user_goal="Run recover task")])
print("DONE", report.results[0].passed)
