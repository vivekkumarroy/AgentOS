import pytest
from unittest.mock import MagicMock
from src.orchestration.orchestrator import Orchestrator
from src.memory.memory import ShortTermMemory
from src.models.state import Plan, Task, TaskStatus

def test_orchestrator_start_and_executable_tasks():
    mock_planner = MagicMock()
    task1 = Task(task_id="t1", description="t1 desc", expected_output="o1")
    task2 = Task(task_id="t2", description="t2 desc", expected_output="o2", dependencies=["t1"])
    plan = Plan(goal="test goal", tasks=[task1, task2])
    
    mock_planner.create_plan.return_value = plan
    
    memory = ShortTermMemory()
    orchestrator = Orchestrator(planner=mock_planner, memory=memory)
    
    state = orchestrator.start("test goal")
    assert state.user_goal == "test goal"
    assert state.current_plan == plan
    
    # t1 has no dependencies, so it should be executable.
    # t2 depends on t1, so it shouldn't be executable.
    executable = orchestrator.get_executable_tasks()
    assert len(executable) == 1
    assert executable[0].task_id == "t1"
    
    # Complete t1
    memory.update_task_status("t1", TaskStatus.COMPLETED)
    
    # t2 should now be executable
    executable = orchestrator.get_executable_tasks()
    assert len(executable) == 1
    assert executable[0].task_id == "t2"
