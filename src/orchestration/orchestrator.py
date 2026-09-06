import logging
from typing import List
from ..planning.planner import Planner
from ..memory.memory import ShortTermMemory
from ..models.state import AgentState, Task, TaskStatus, ToolCall
from ..execution.executor import Executor
from ..verification.verifier import VerificationEngine
from ..recovery.diagnosis import FailureDiagnosisEngine
from ..recovery.replanner import RecoveryPlanner
from ..recovery.circuit_breaker import CircuitBreaker
from ..models.state import TaskStatus, Observation
from ..config import settings
from ..tracing.tracer import Tracer, NoOpTracer
from ..tracing.events import TraceEvent, EventType
import uuid
import time

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, 
                 planner: Planner, 
                 memory: ShortTermMemory, 
                 executor: Executor = None,
                 verifier: VerificationEngine = None,
                 diagnoser: FailureDiagnosisEngine = None,
                 replanner: RecoveryPlanner = None,
                 circuit_breaker: CircuitBreaker = None,
                 tracer: Tracer = None):
        self.planner = planner
        self.memory = memory
        self.executor = executor
        self.verifier = verifier
        self.diagnoser = diagnoser
        self.replanner = replanner
        self.circuit_breaker = circuit_breaker
        self.tracer = tracer or NoOpTracer()

    def start(self, goal: str) -> AgentState:
        """Starts the orchestration process by taking a goal, planning, and setting memory."""
        logger.info(f"Orchestrator received new goal: {goal}")
        
        self.memory.set_goal(goal)
        state = self.memory.get_state()
        if "run_id" not in state.execution_context:
            state.execution_context["run_id"] = str(uuid.uuid4())
        
        run_id = state.execution_context["run_id"]
        self.tracer.emit(TraceEvent(
            run_id=run_id,
            task_id="system",
            event_type=EventType.RUN_STARTED,
            status="SUCCESS",
            metadata={"goal": goal}
        ))
        
        try:
            self.tracer.emit(TraceEvent(
                run_id=run_id,
                task_id="system",
                event_type=EventType.PLANNING,
                status="STARTED"
            ))
            plan = self.planner.create_plan(goal)
            self.memory.set_plan(plan)
            self.tracer.emit(TraceEvent(
                run_id=run_id,
                task_id="system",
                event_type=EventType.PLANNING,
                status="COMPLETED",
                metadata={"plan_tasks": len(plan.tasks)}
            ))
            
            if not plan.tasks:
                self.tracer.emit(TraceEvent(
                    run_id=run_id,
                    task_id="system",
                    event_type=EventType.RUN_COMPLETED,
                    status="SUCCESS",
                    metadata={"final_status": "SUCCESS", "total_tasks": 0}
                ))
                state.execution_context["run_completed_emitted"] = True
                
            return self.memory.get_state()
        except Exception as e:
            logger.error(f"Orchestration failed during planning phase: {e}")
            raise

    def get_executable_tasks(self) -> List[Task]:
        """Determine tasks that have all their dependencies met and are PENDING."""
        state = self.memory.get_state()
        if not state.current_plan:
            return []

        executable_tasks = []
        for task_id, task in state.tasks_state.items():
            if task.status == TaskStatus.PENDING:
                can_execute = True
                for dep_id in task.dependencies:
                    dep_task = state.tasks_state.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        can_execute = False
                        break
                
                if can_execute:
                    executable_tasks.append(task)
                    
        return executable_tasks

    def execute_task_with_tool(self, task_id: str, tool_call: ToolCall):
        """Execute a tool for a given task and update memory with the observation."""
        if not self.executor:
            raise ValueError("Executor is not configured for this Orchestrator instance.")
            
        logger.info(f"Executing task {task_id} with tool {tool_call.tool_name}")
        self.memory.update_task_status(task_id, TaskStatus.RUNNING)
        
        observation = self.executor.execute_tool(tool_call)
        
        self.memory.add_observation(observation)
        
        if observation.status == "SUCCESS":
            self.memory.update_task_status(task_id, TaskStatus.COMPLETED)
        else:
            self.memory.update_task_status(task_id, TaskStatus.FAILED)
            
        return observation

    def run_task_with_recovery(self, task_id: str) -> Task:
        """Executes a task through the complete Phase 3 recovery loop."""
        state = self.memory.get_state()
        if task_id not in state.tasks_state:
            raise ValueError(f"Task {task_id} not found in memory.")
            
        task = state.tasks_state[task_id]
        run_id = state.execution_context.get("run_id", "unknown_run")
        delegation_depth = state.execution_context.get("delegation_depth", 0)
        from ..tracing.context import current_run_id, current_delegation_depth
        token_run_id = current_run_id.set(run_id)
        token_depth = current_delegation_depth.set(delegation_depth)
        try:

            while task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                self.memory.update_task_status(task.task_id, TaskStatus.RUNNING)
                logger.info(f"TASK_STARTED: {task.task_id} (Attempt {task.retry_count + 1})")
                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_STARTED, status="STARTED", metadata={"retry_count": task.retry_count}))

                try:
                    available_schemas = self.executor.registry.get_all_schemas() if self.executor else []
                    tool_call = self.planner.generate_tool_call(task, available_schemas)
                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TOOL_SELECTED, status="COMPLETED", metadata={"tool_name": tool_call.tool_name}))
                except Exception as e:
                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.FAILURE, status="ERROR", metadata={"error": str(e)}))
                    self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                    break

                if self.circuit_breaker and self.circuit_breaker.check_loop(tool_call, state.action_history):
                    logger.warning("CIRCUIT_BREAKER_TRIGGERED")
                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.FAILURE, status="ERROR", metadata={"reason": "Circuit breaker triggered"}))
                    self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                    break

                logger.info("TOOL_EXECUTED")
                state.action_history.append(tool_call)
                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TOOL_EXECUTION_STARTED, status="STARTED", metadata={"tool_name": tool_call.tool_name}))

                t0 = time.time()
                observation = self.executor.execute_tool(tool_call)
                duration = time.time() - t0

                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TOOL_EXECUTION_COMPLETED, status=observation.status, metadata={"tool_name": tool_call.tool_name, "duration": duration}))
                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.OBSERVATION, status="COMPLETED", metadata={"observation_status": observation.status}))
                self.memory.add_observation(observation)

                if self.verifier:
                    self.memory.update_task_status(task.task_id, TaskStatus.VERIFYING)
                    logger.info("VERIFICATION_STARTED")
                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.VERIFICATION, status="STARTED"))
                    verification = self.verifier.verify(task, tool_call, observation)
                    task.verification_result = verification
                    logger.info(f"VERIFICATION_RESULT: {verification.success}")
                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.VERIFICATION, status="COMPLETED", metadata={"success": verification.success, "reason": verification.reason}))

                    if verification.success:
                        self.memory.update_task_status(task.task_id, TaskStatus.COMPLETED)
                        logger.info("TASK_COMPLETED")
                        self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_COMPLETED, status="SUCCESS"))
                        break
                    else:
                        logger.warning("FAILURE_DETECTED")
                        self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.FAILURE, status="DETECTED", metadata={"reason": verification.reason}))
                        if self.diagnoser:
                            self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.DIAGNOSIS, status="STARTED"))
                            diagnosis = self.diagnoser.diagnose(task, observation, verification)
                            task.diagnosis = diagnosis
                            logger.info("FAILURE_DIAGNOSED")
                            self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.DIAGNOSIS, status="COMPLETED", metadata={"failure_type": diagnosis.failure_type}))

                            if self.replanner:
                                self.memory.update_task_status(task.task_id, TaskStatus.REPLANNING)
                                logger.info("RECOVERY_STARTED")
                                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.RECOVERY_PLANNING, status="STARTED"))

                                task.retry_count += 1

                                recovery_plan = self.replanner.create_recovery_plan(task, diagnosis)
                                task.recovery_plan = recovery_plan
                                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.RECOVERY_PLANNING, status="COMPLETED", metadata={"strategy": recovery_plan.strategy, "retry_allowed": recovery_plan.retry_allowed}))

                                if recovery_plan.retry_allowed:
                                    task.description = recovery_plan.revised_task_description
                                    logger.info("RETRY_STARTED")
                                    self.memory.update_task_status(task.task_id, TaskStatus.PENDING)
                                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.RETRY, status="STARTED", metadata={"retry_count": task.retry_count}))
                                    continue
                                else:
                                    self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                                    logger.error("TASK_FAILED: Unrecoverable or Budget Exhausted")
                                    self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_FAILED, status="FAILED", metadata={"reason": "Unrecoverable or Budget Exhausted"}))
                                    break
                            else:
                                self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                                self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_FAILED, status="FAILED", metadata={"reason": "No replanner"}))
                                break
                        else:
                            self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                            self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_FAILED, status="FAILED", metadata={"reason": "No diagnoser"}))
                            break
                else:
                    if observation.status == "SUCCESS":
                        self.memory.update_task_status(task.task_id, TaskStatus.COMPLETED)
                        self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_COMPLETED, status="SUCCESS"))
                    else:
                        self.memory.update_task_status(task.task_id, TaskStatus.FAILED)
                        self.tracer.emit(TraceEvent(run_id=run_id, task_id=task.task_id, event_type=EventType.TASK_FAILED, status="FAILED"))
                    break

            # Check if the overall run is finished
            active_states = {TaskStatus.RUNNING, TaskStatus.VERIFYING, TaskStatus.REPLANNING}
            has_active = any(t.status in active_states for t in state.tasks_state.values())

            if not has_active and not self.get_executable_tasks():
                if not state.execution_context.get("run_completed_emitted"):
                    has_failed = any(t.status == TaskStatus.FAILED for t in state.tasks_state.values())
                    final_status = "FAILED" if has_failed else "SUCCESS"

                    self.tracer.emit(TraceEvent(
                        run_id=run_id,
                        task_id="system",
                        event_type=EventType.RUN_COMPLETED,
                        status=final_status,
                        metadata={
                            "final_status": final_status, 
                            "total_tasks": len(state.tasks_state)
                        }
                    ))
                    state.execution_context["run_completed_emitted"] = True

            return task
        finally:
            current_run_id.reset(token_run_id)
            current_delegation_depth.reset(token_depth)
