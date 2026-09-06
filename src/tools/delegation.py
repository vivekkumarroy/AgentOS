import json
from typing import Any
from pydantic import BaseModel, Field
from .base import BaseTool
from ..orchestration.registry import AgentRegistry
from ..orchestration.factory import SubAgentFactory
from ..tracing.context import current_run_id, current_delegation_depth
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class DelegateTaskArgs(BaseModel):
    agent_name: str = Field(..., description="Name of the specialized agent to delegate to.")
    task_description: str = Field(..., description="Detailed description of the task for the specialized agent.")

class DelegateTaskTool(BaseTool):
    name = "delegate_task"
    description = "Delegates a specific sub-task to a specialized worker agent."
    input_schema = DelegateTaskArgs

    def __init__(self, registry: AgentRegistry, factory: SubAgentFactory):
        self.registry = registry
        self.factory = factory

    def execute(self, **kwargs: Any) -> Any:
        agent_name = kwargs.get("agent_name")
        task_description = kwargs.get("task_description")

        # 1. Lookup agent
        profile = self.registry.get(agent_name)
        if not profile:
            return {"success": False, "error": f"Agent '{agent_name}' is not registered."}

        # 2. Check delegation depth
        parent_depth = current_delegation_depth.get()
        if parent_depth >= settings.max_delegation_depth:
            return {"success": False, "error": f"Max delegation depth ({settings.max_delegation_depth}) reached. Cannot delegate further."}

        # 3. Get parent run_id
        parent_run_id = current_run_id.get()
        if not parent_run_id:
            return {"success": False, "error": "No active run_id in context. Cannot correlate trace."}

        # 4. Create worker
        try:
            worker = self.factory.create_worker(
                profile=profile,
                parent_run_id=parent_run_id,
                delegation_depth=parent_depth + 1
            )
        except Exception as e:
            return {"success": False, "error": f"Failed to create worker agent: {e}"}

        # 5. Execute task
        try:
            final_state = worker.start(task_description)
            # The start() method runs planning, then we must run executable tasks.
            # Wait, start() just plans. We need to actually run the task.
            # We can get the first (and only) task from the plan and run it.
            if not final_state.current_plan or not final_state.current_plan.tasks:
                return {"success": True, "result": "Worker generated empty plan."}
            
            # Since the worker is autonomous, it might have multiple tasks. We should run all of them.
            # But the orchestrator doesn't have a "run_all" method natively exposed that does dependency resolution
            # in a while loop. Let's look at `api.py` `execute_task_endpoint` - it calls `run_task_with_recovery` 
            # for a specific task. We can just execute the tasks sequentially.
            results = []
            for task in final_state.current_plan.tasks:
                completed_task = worker.run_task_with_recovery(task.task_id)
                results.append({
                    "task": task.description,
                    "status": completed_task.status,
                    "output": completed_task.expected_output if completed_task.status == "COMPLETED" else "Failed"
                })
            
            # Extract final observations
            obs_summaries = [obs.result for obs in final_state.observations]
            
            return {
                "success": True,
                "result": f"Delegation completed. Worker tasks: {json.dumps(results)}. Final observations: {json.dumps(obs_summaries)}"
            }
            
        except Exception as e:
            logger.error(f"Worker agent failed: {e}")
            return {"success": False, "error": f"Worker agent execution failed: {str(e)}"}
