import pytest
from src.memory.memory import ShortTermMemory
from src.models.state import Plan, Task, Observation, TaskStatus

def test_memory_operations():
    memory = ShortTermMemory()
    
    # Test set goal
    memory.set_goal("Test Goal")
    assert memory.get_state().user_goal == "Test Goal"
    
    # Test set plan
    task = Task(task_id="t1", description="Desc", expected_output="Out")
    plan = Plan(goal="Test Goal", tasks=[task])
    memory.set_plan(plan)
    
    state = memory.get_state()
    assert state.current_plan == plan
    assert "t1" in state.tasks_state
    
    # Test update status
    memory.update_task_status("t1", TaskStatus.COMPLETED)
    assert memory.get_state().tasks_state["t1"].status == TaskStatus.COMPLETED
    
    # Test observation
    obs = Observation(result="Res", status="OK")
    memory.add_observation(obs)
    assert len(memory.get_state().observations) == 1
    
    # Test clear
    memory.clear()
    assert memory.get_state().user_goal == ""
    assert memory.get_state().current_plan is None
