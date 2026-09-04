from src.recovery.circuit_breaker import CircuitBreaker
from src.models.state import ToolCall

def test_circuit_breaker():
    cb = CircuitBreaker(max_identical_actions=3)
    
    call1 = ToolCall(tool_name="test", arguments={"a": 1})
    call2 = ToolCall(tool_name="test", arguments={"a": 2})
    
    history = [call1, call1]
    
    # 3rd identical call
    assert cb.check_loop(call1, history) is True
    
    # Different call
    assert cb.check_loop(call2, history) is False
