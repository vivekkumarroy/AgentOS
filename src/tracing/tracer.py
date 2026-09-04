from abc import ABC, abstractmethod
from typing import List, Any
import json
import os
from pathlib import Path
import logging
from .events import TraceEvent

logger = logging.getLogger(__name__)

class Tracer(ABC):
    @abstractmethod
    def emit(self, event: TraceEvent):
        pass
        
    @abstractmethod
    def get_traces(self, task_id: str) -> List[TraceEvent]:
        pass

class NoOpTracer(Tracer):
    def emit(self, event: TraceEvent):
        pass
        
    def get_traces(self, task_id: str) -> List[TraceEvent]:
        return []

class LocalTracer(Tracer):
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path).resolve()
        self.redact_keys = {"api_key", "password", "token", "secret", "authorization"}
        
        # Ensure dir exists
        os.makedirs(self.storage_path.parent, exist_ok=True)

    def _redact(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: ("***REDACTED***" if any(r in k.lower() for r in self.redact_keys) else self._redact(v)) 
                    for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact(i) for i in data]
        return data

    def emit(self, event: TraceEvent):
        redacted_meta = self._redact(event.metadata)
        event_dict = event.model_dump()
        event_dict["metadata"] = redacted_meta
        
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to write trace event: {e}")

    def get_traces(self, task_id: str) -> List[TraceEvent]:
        traces = []
        if not self.storage_path.exists():
            return traces
            
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("task_id") == task_id:
                            traces.append(TraceEvent(**data))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to read traces: {e}")
            
        return traces
