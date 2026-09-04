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
        if "success" in goal.lower():
            return Plan(goal=goal, tasks=[Task(task_id="t1", description="Success task", expected_output="ok", status=TaskStatus.PENDING)])
        elif "fail" in goal.lower():
            return Plan(goal=goal, tasks=[Task(task_id="t2", description="Fail task", expected_output="ok", status=TaskStatus.PENDING)])
        elif "recover" in goal.lower():
            return Plan(goal=goal, tasks=[Task(task_id="t3", description="Recover task", expected_output="ok", status=TaskStatus.PENDING)])

    def generate_tool_call(self, task, schemas):
        if task.task_id == "t1": return ToolCall(tool_name="write_file", arguments={})
        elif task.task_id == "t2": return ToolCall(tool_name="read_file", arguments={})
        elif task.task_id == "t3":
            if task.retry_count == 0: return ToolCall(tool_name="failing_tool", arguments={})
            else: return ToolCall(tool_name="write_file", arguments={})

class DummyRegistry:
    def get_all_schemas(self): return []

class MockExecutor:
    def __init__(self): self.registry = DummyRegistry()
    def execute_tool(self, call: ToolCall):
        if call.tool_name == "write_file": return Observation(result="File written", status="SUCCESS")
        elif call.tool_name == "read_file": return Observation(result="File not found", status="ERROR")
        elif call.tool_name == "failing_tool": return Observation(result="Tool failed", status="ERROR")
            
class MockVerifier:
    def verify(self, task, tool_call, obs):
        if obs.status == "SUCCESS": return VerificationResult(success=True, reason="Looks good")
        return VerificationResult(success=False, reason="Tool error")

class MockDiagnoser:
    def diagnose(self, task, obs, verif):
        return FailureDiagnosis(failure_type=FailureCategory.TOOL_ERROR, reason="Tool failed", affected_task_id=task.task_id, recoverable=True, suggested_recovery="Try another tool")

class MockReplanner:
    def create_recovery_plan(self, task, diag):
        return RecoveryPlan(original_task_id=task.task_id, strategy="Retry with different tool", revised_task_description="Try writing file instead", retry_allowed=(task.retry_count < 2))

def verify():
    print("--- VERIFYING PHASE 5 ---")
    tracer = LocalTracer("./data/traces.jsonl")
    evaluator = Evaluator(MockPlanner(), MockExecutor(), MockVerifier(), MockDiagnoser(), MockReplanner(), None, tracer)
    cases = [
        TestCase(case_id="eval_success", user_goal="Run success task", expected_tools=["write_file"], expected_result="File written"),
        TestCase(case_id="eval_fail", user_goal="Run fail task", expected_tools=["read_file"]),
        TestCase(case_id="eval_recovery", user_goal="Run recover task", expected_tools=["write_file"])
    ]
    report = evaluator.evaluate(cases)
    print("Total Cases:", report.total_cases)
    print("Passed Cases:", report.passed_cases)
    for r in report.results: print(f"{r.case_id}: passed={r.passed}")

if __name__ == "__main__":
    verify()
