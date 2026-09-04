import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from src.planning.planner import Planner
from src.models.state import Plan, Task

def test_planner_success():
    mock_llm = MagicMock()
    task = Task(task_id="t1", description="desc", expected_output="out")
    mock_llm.generate_structured_output.return_value = Plan(goal="goal", tasks=[task])
    
    planner = Planner(llm_client=mock_llm)
    plan = planner.create_plan("do something")
    
    assert plan.goal == "goal"
    assert len(plan.tasks) == 1
    assert plan.tasks[0].task_id == "t1"
    mock_llm.generate_structured_output.assert_called_once()

def test_planner_validation_error():
    mock_llm = MagicMock()
    # Create a mock ValidationError
    try:
        Plan(tasks=[])  # missing goal triggers ValidationError
    except ValidationError as e:
        error = e
        
    mock_llm.generate_structured_output.side_effect = error
    
    planner = Planner(llm_client=mock_llm)
    with pytest.raises(ValueError, match="LLM produced an invalid plan structure"):
        planner.create_plan("do something")
