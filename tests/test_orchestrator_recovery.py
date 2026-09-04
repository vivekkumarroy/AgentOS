from src.orchestration.orchestrator import Orchestrator
from src.planning.planner import Planner
from src.memory.memory import ShortTermMemory
from src.models.state import Task, TaskStatus, ToolCall, Observation, VerificationResult, FailureDiagnosis, FailureCategory, RecoveryPlan
from src.recovery.circuit_breaker import CircuitBreaker

class MockRegistry:
    def get_all_schemas(self):
        return []

class MockExecutor:
    def __init__(self, observations):
        self.observations = observations
        self.call_count = 0
        self.registry = MockRegistry()
    def execute_tool(self, call):
        obs = self.observations[self.call_count]
        self.call_count += 1
        return obs
        
class MockPlanner(Planner):
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls
        self.call_count = 0
    def generate_tool_call(self, task, schemas):
        tc = self.tool_calls[self.call_count]
        self.call_count += 1
        return tc
        
class MockVerifier:
    def __init__(self, results):
        self.results = results
        self.call_count = 0
    def verify(self, task, tool, obs):
        res = self.results[self.call_count]
        self.call_count += 1
        return res
        
class MockDiagnoser:
    def __init__(self, diags):
        self.diags = diags
        self.call_count = 0
    def diagnose(self, task, obs, ver):
        diag = self.diags[self.call_count]
        self.call_count += 1
        return diag
        
class MockReplanner:
    def __init__(self, plans):
        self.plans = plans
        self.call_count = 0
    def create_recovery_plan(self, task, diag):
        plan = self.plans[self.call_count]
        self.call_count += 1
        return plan

def test_orchestrator_recovery_flow():
    task = Task(task_id="t1", description="d", expected_output="o")
    mem = ShortTermMemory()
    mem.get_state().tasks_state["t1"] = task
    
    tc1 = ToolCall(tool_name="t1")
    tc2 = ToolCall(tool_name="t2")
    planner = MockPlanner([tc1, tc2])
    
    obs1 = Observation(status="SUCCESS", result="bad")
    obs2 = Observation(status="SUCCESS", result="good")
    executor = MockExecutor([obs1, obs2])
    
    ver1 = VerificationResult(success=False, reason="bad")
    ver2 = VerificationResult(success=True, reason="good")
    verifier = MockVerifier([ver1, ver2])
    
    diag1 = FailureDiagnosis(failure_type=FailureCategory.UNKNOWN_ERROR, reason="r", affected_task_id="t1", recoverable=True, suggested_recovery="s")
    diagnoser = MockDiagnoser([diag1])
    
    plan1 = RecoveryPlan(original_task_id="t1", strategy="s", revised_task_description="new", retry_allowed=True)
    replanner = MockReplanner([plan1])
    
    cb = CircuitBreaker()
    
    orch = Orchestrator(planner, mem, executor, verifier, diagnoser, replanner, cb)
    
    final_task = orch.run_task_with_recovery("t1")
    
    assert final_task.status == TaskStatus.COMPLETED
    assert final_task.retry_count == 1
    assert planner.call_count == 2
