import pytest
import os
import json
from src.tracing.events import TraceEvent, EventType
from src.tracing.tracer import NoOpTracer, LocalTracer
import tempfile

def test_trace_event_serialization():
    event = TraceEvent(
        run_id="run1",
        task_id="task1",
        event_type=EventType.RUN_STARTED,
        status="SUCCESS",
        metadata={"key": "value"}
    )
    d = event.model_dump()
    assert d["run_id"] == "run1"
    assert "event_id" in d

def test_noop_tracer():
    tracer = NoOpTracer()
    tracer.emit(TraceEvent(run_id="r", task_id="t", event_type=EventType.RUN_STARTED, status="S"))
    assert len(tracer.get_traces("t")) == 0

def test_local_tracer_storage_and_redaction():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "traces.jsonl")
        tracer = LocalTracer(storage_path)
        
        tracer.emit(TraceEvent(
            run_id="r1",
            task_id="t1",
            event_type=EventType.TASK_STARTED,
            status="STARTED",
            metadata={"safe": "data", "api_key": "secret123", "nested": {"password": "pwd"}}
        ))
        
        tracer.emit(TraceEvent(
            run_id="r1",
            task_id="t2",
            event_type=EventType.TASK_STARTED,
            status="STARTED"
        ))
        
        t1_traces = tracer.get_traces("t1")
        assert len(t1_traces) == 1
        assert t1_traces[0].task_id == "t1"
        assert t1_traces[0].metadata["safe"] == "data"
        assert t1_traces[0].metadata["api_key"] == "***REDACTED***"
        assert t1_traces[0].metadata["nested"]["password"] == "***REDACTED***"
        
        t2_traces = tracer.get_traces("t2")
        assert len(t2_traces) == 1
