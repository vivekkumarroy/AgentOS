import pytest
from pydantic import ValidationError
from src.models.state import Task, Plan, Observation, TaskStatus, PlanStatus, AgentState

def test_valid_task():
    task = Task(task_id="t1", description="Do something", expected_output="Done")
    assert task.task_id == "t1"
    assert task.status == TaskStatus.PENDING
    assert task.dependencies == []

def test_invalid_task():
    with pytest.raises(ValidationError):
        Task(description="Missing task_id and expected_output")

def test_valid_plan():
    task = Task(task_id="t1", description="Do something", expected_output="Done")
    plan = Plan(goal="Test goal", tasks=[task])
    assert plan.goal == "Test goal"
    assert len(plan.tasks) == 1
    assert plan.status == PlanStatus.IN_PROGRESS

def test_invalid_plan():
    with pytest.raises(ValidationError):
        Plan(tasks=[])  # missing goal

def test_valid_observation():
    obs = Observation(result="Found 42", status="SUCCESS")
    assert obs.result == "Found 42"
    assert obs.error is None

def test_invalid_observation():
    with pytest.raises(ValidationError):
        Observation(result="Missing status")

def test_valid_agent_state():
    state = AgentState(user_goal="My goal")
    assert state.user_goal == "My goal"
    assert state.status == "IDLE"
