import pytest
from src.orchestration.orchestrator import Orchestrator
from src.memory.memory import ShortTermMemory
from src.tracing.events import EventType
from src.models.state import Task, TaskStatus, Plan, Observation

class MockPlanner:
    def __init__(self, plan: Plan):
        self.plan = plan
        
    def create_plan(self, goal: str) -> Plan:
        return self.plan
        
    def generate_tool_call(self, task: Task, schemas: list):
        from src.models.state import ToolCall
        return ToolCall(tool_name="mock_tool", arguments={})

class MockExecutor:
    def __init__(self):
        from src.tools.registry import ToolRegistry
        self.registry = ToolRegistry()
        
    def execute_tool(self, call):
        return Observation(result="success", status="SUCCESS")

class MockTracer:
    def __init__(self):
        self.events = []
        
    def emit(self, event):
        self.events.append(event)
        
    def get_traces(self, task_id: str):
        if task_id == "system":
            return [e for e in self.events if e.task_id == "system"]
        return [e for e in self.events if e.task_id == task_id]

def test_run_completed_emitted():
    # Setup
    plan = Plan(goal="test", tasks=[
        Task(task_id="task_1", description="desc 1", expected_output="out 1")
    ])
    planner = MockPlanner(plan)
    executor = MockExecutor()
    memory = ShortTermMemory()
    tracer = MockTracer()
    
    orchestrator = Orchestrator(
        planner=planner,
        executor=executor,
        memory=memory,
        tracer=tracer
    )
    
    state = orchestrator.start("test run")
    
    # RUN_COMPLETED should not be emitted yet because there are tasks
    system_events = [e.event_type for e in tracer.events if e.task_id == "system"]
    assert EventType.RUN_COMPLETED not in system_events
    
    executable = orchestrator.get_executable_tasks()
    assert len(executable) == 1
    
    # Run the single task
    orchestrator.run_task_with_recovery("task_1")
    
    # Now it should be completed and emit RUN_COMPLETED
    system_events = [e.event_type for e in tracer.events if e.task_id == "system"]
    assert EventType.RUN_COMPLETED in system_events
    
    run_completed_event = [e for e in tracer.events if e.event_type == EventType.RUN_COMPLETED][0]
    assert run_completed_event.status == "SUCCESS"
    assert run_completed_event.metadata["total_tasks"] == 1
    
    # Calling it again shouldn't emit a duplicate
    orchestrator.run_task_with_recovery("task_1")
    run_completed_events = [e for e in tracer.events if e.event_type == EventType.RUN_COMPLETED]
    assert len(run_completed_events) == 1

def test_run_completed_empty_plan():
    # Setup
    plan = Plan(goal="test", tasks=[])
    planner = MockPlanner(plan)
    memory = ShortTermMemory()
    tracer = MockTracer()
    
    orchestrator = Orchestrator(
        planner=planner,
        memory=memory,
        tracer=tracer
    )
    
    state = orchestrator.start("test empty plan")
    
    # RUN_COMPLETED should be emitted immediately
    system_events = [e.event_type for e in tracer.events if e.task_id == "system"]
    assert EventType.RUN_COMPLETED in system_events
    
    run_completed_event = [e for e in tracer.events if e.event_type == EventType.RUN_COMPLETED][0]
    assert run_completed_event.status == "SUCCESS"
    assert run_completed_event.metadata["total_tasks"] == 0

def test_run_completed_failed_task():
    # Setup
    plan = Plan(goal="test", tasks=[
        Task(task_id="task_1", description="desc 1", expected_output="out 1")
    ])
    planner = MockPlanner(plan)
    
    class FailedMockExecutor:
        def __init__(self):
            from src.tools.registry import ToolRegistry
            self.registry = ToolRegistry()
        def execute_tool(self, call):
            return Observation(result="fail", status="ERROR")
            
    executor = FailedMockExecutor()
    memory = ShortTermMemory()
    tracer = MockTracer()
    
    orchestrator = Orchestrator(
        planner=planner,
        executor=executor,
        memory=memory,
        tracer=tracer
    )
    
    state = orchestrator.start("test run fail")
    orchestrator.run_task_with_recovery("task_1")
    
    system_events = [e.event_type for e in tracer.events if e.task_id == "system"]
    assert EventType.RUN_COMPLETED in system_events
    
    run_completed_event = [e for e in tracer.events if e.event_type == EventType.RUN_COMPLETED][0]
    assert run_completed_event.status == "FAILED"
