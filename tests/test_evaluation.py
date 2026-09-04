import pytest
from src.evaluation.models import TestCase
from src.evaluation.framework import Evaluator
from src.tracing.tracer import NoOpTracer

class MockPlanner:
    def create_plan(self, goal):
        from src.models.state import Plan, Task
        return Plan(goal=goal, tasks=[Task(task_id="t1", description="do stuff", expected_output="done")])
    def generate_tool_call(self, task, schemas):
        from src.models.state import ToolCall
        return ToolCall(tool_name="mock_tool", arguments={})

class MockExecutor:
    def __init__(self):
        from src.tools.registry import ToolRegistry
        self.registry = ToolRegistry()
    def execute_tool(self, call):
        from src.models.state import Observation
        return Observation(result="Mock success", status="SUCCESS")

def test_evaluation_success():
    planner = MockPlanner()
    executor = MockExecutor()
    
    evaluator = Evaluator(
        planner=planner,
        executor=executor,
        verifier=None,
        diagnoser=None,
        replanner=None,
        circuit_breaker=None,
        tracer=NoOpTracer()
    )
    
    cases = [
        TestCase(
            case_id="c1",
            user_goal="Test goal",
            expected_result="Mock success"
        )
    ]
    
    report = evaluator.evaluate(cases)
    assert report.total_cases == 1
    assert report.passed_cases == 1
    assert report.success_rate == 1.0
    assert report.results[0].passed == True

def test_evaluation_failure():
    planner = MockPlanner()
    executor = MockExecutor()
    evaluator = Evaluator(planner, executor, None, None, None, None, NoOpTracer())
    
    cases = [
        TestCase(
            case_id="c2",
            user_goal="Fail goal",
            expected_tools=["missing_tool"]
        )
    ]
    
    report = evaluator.evaluate(cases)
    assert report.passed_cases == 0
    assert report.results[0].passed == False
    assert "Missing expected tools" in report.results[0].failure_reason
