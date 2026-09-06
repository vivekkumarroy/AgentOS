import pytest
import time
from fastapi.testclient import TestClient
from src.api import app
from src.config import Settings
from src.tracing.tracer import LocalTracer
from src.tracing.events import TraceEvent, EventType
import tempfile
import os

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "environment" not in response.json()

def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_global_exception_handler():
    # We can trigger a ValueError by sending bad JSON to an endpoint
    response = client.post("/tools/execute", json={"invalid": "data"})
    assert response.status_code == 422 # Pydantic validation error

def test_config_validation():
    # Test fallback clamping for negative timeouts
    s = Settings(timeout=-10, max_task_retries=0, max_delegation_depth=-5)
    assert s.timeout == 1
    assert s.max_task_retries == 1
    assert s.max_delegation_depth == 1
    
    # Test string parsing
    s2 = Settings(timeout="10")
    assert s2.timeout == 10

def test_tracer_truncation():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracer_path = os.path.join(tmpdir, "traces.jsonl")
        tracer = LocalTracer(tracer_path)
        
        # Create a massive string
        massive_string = "A" * 15000
        event = TraceEvent(
            run_id="r1",
            task_id="t1",
            event_type=EventType.TASK_STARTED,
            status="STARTED",
            metadata={"large_data": massive_string}
        )
        
        tracer.emit(event)
        
        traces = tracer.get_traces("t1")
        assert len(traces) == 1
        stored_string = traces[0].metadata["large_data"]
        assert len(stored_string) < 11000
        assert stored_string.endswith("[TRUNCATED]")
