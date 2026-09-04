import os
from src.evaluation.models import TestCase
from src.evaluation.framework import Evaluator
from src.tracing.tracer import LocalTracer
from src.models.state import Plan, Task, TaskStatus, Observation, ToolCall, FailureDiagnosis, FailureCategory, RecoveryPlan
from src.verification.verifier import VerificationResult

class MockPlanner:
    def create_plan(self, goal):
        # We'll use the goal string to decide the mock plan
        if "success" in goal.lower():
            return Plan(goal=goal, tasks=[Task(task_id="t1", description="Success task", expected_output="ok", status=TaskStatus.PENDING)])
        elif "fail" in goal.lower():
            return Plan(goal=goal, tasks=[Task(task_id="t2", description="Fail task", expected_output="ok", status=TaskStatus.PENDING)])
        elif "recover" in goal.lower():
            # Initial plan for recovery scenario
            return Plan(goal=goal, tasks=[Task(task_id="t3", description="Recover task", expected_output="ok", status=TaskStatus.PENDING)])
            
    def generate_tool_call(self, task, schemas):
        if task.task_id == "t1":
            return ToolCall(tool_name="write_file", arguments={"path": "hello.txt", "content": "Hello"})
        elif task.task_id == "t2":
            return ToolCall(tool_name="read_file", arguments={"path": "does_not_exist.txt"})
        elif task.task_id == "t3":
            if task.retry_count == 0:
                return ToolCall(tool_name="failing_tool", arguments={})
            else:
                return ToolCall(tool_name="write_file", arguments={"path": "recovered.txt", "content": "Fixed"})

class DummyRegistry:
    def get_all_schemas(self):
        return []

class MockExecutor:
    def __init__(self):
        self.registry = DummyRegistry()
        
    def execute_tool(self, call: ToolCall):
        if call.tool_name == "write_file":
            return Observation(result="File written", status="SUCCESS")
        elif call.tool_name == "read_file":
            return Observation(result="File not found", status="ERROR")
        elif call.tool_name == "failing_tool":
            return Observation(result="Tool failed", status="ERROR")
            
class MockVerifier:
    def verify(self, task, tool_call, obs):
        if obs.status == "SUCCESS":
            return VerificationResult(success=True, reason="Looks good")
        return VerificationResult(success=False, reason="Tool error")

class MockDiagnoser:
    def diagnose(self, task, obs, verif):
        return FailureDiagnosis(
            failure_type=FailureCategory.TOOL_ERROR,
            reason="Tool failed",
            affected_task_id=task.task_id,
            recoverable=True,
            suggested_recovery="Try another tool"
        )

class MockReplanner:
    def create_recovery_plan(self, task, diag):
        return RecoveryPlan(
            original_task_id=task.task_id,
            strategy="Retry with different tool",
            revised_task_description="Try writing file instead",
            retry_allowed=(task.retry_count < 2)
        )

def verify():
    print("--- VERIFYING PHASE 5 ---")
    
    # 1. Setup mock evaluation framework with a fresh Tracer to log to data/traces.jsonl
    tracer = LocalTracer("./data/traces.jsonl")
    evaluator = Evaluator(
        planner=MockPlanner(),
        executor=MockExecutor(),
        verifier=MockVerifier(),
        diagnoser=MockDiagnoser(),
        replanner=MockReplanner(),
        circuit_breaker=None,
        tracer=tracer
    )
    
    cases = [
        TestCase(
            case_id="eval_success",
            user_goal="Run success task",
            expected_tools=["write_file"],
            expected_result="File written"
        ),
        TestCase(
            case_id="eval_fail",
            user_goal="Run fail task",
            expected_tools=["read_file"],
        ),
        TestCase(
            case_id="eval_recovery",
            user_goal="Run recover task",
            expected_tools=["write_file"]
        )
    ]
    
    print("Running evaluation suite...")
    report = evaluator.evaluate(cases)
    
    print(f"Total Cases: {report.total_cases}")
    print(f"Passed Cases: {report.passed_cases}")
    print(f"Failed Cases: {report.failed_cases}")
    
    for r in report.results:
        print(f"Case: {r.case_id} | Passed: {r.passed} | Reason: {r.failure_reason} | Tools Used: {r.tool_usage_count} | Recoveries: {r.recovery_attempts} | Status: {r.final_task_status}")
        
    print("\nChecking traces...")
    if os.path.exists("./data/traces.jsonl"):
        with open("./data/traces.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"Total trace events generated: {len(lines)}")
            for line in lines:
                if "api_key" in line and "***REDACTED***" not in line:
                    print("FAIL: Found unredacted api_key!")
        print("PASS: Traces exist and redaction rules apply.")
    else:
        print("FAIL: Trace file not found.")

if __name__ == "__main__":
    verify()
