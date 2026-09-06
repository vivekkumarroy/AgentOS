import time
import os
from typing import List, Dict, Any
from .models import TestCase, EvalResult, EvalReport
from ..orchestration.orchestrator import Orchestrator
from ..memory.memory import ShortTermMemory
from ..planning.planner import Planner
from ..execution.executor import Executor
from ..verification.verifier import VerificationEngine
from ..recovery.diagnosis import FailureDiagnosisEngine
from ..recovery.replanner import RecoveryPlanner
from ..recovery.circuit_breaker import CircuitBreaker
from ..tracing.tracer import Tracer
from ..tracing.events import EventType
from ..config import settings

class Evaluator:
    def __init__(self, 
                 planner: Planner,
                 executor: Executor,
                 verifier: VerificationEngine,
                 diagnoser: FailureDiagnosisEngine,
                 replanner: RecoveryPlanner,
                 circuit_breaker: CircuitBreaker,
                 tracer: Tracer):
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.diagnoser = diagnoser
        self.replanner = replanner
        self.circuit_breaker = circuit_breaker
        self.tracer = tracer

    def evaluate(self, cases: List[TestCase]) -> EvalReport:
        results = []
        total_time = 0
        total_tools = 0
        total_recoveries = 0
        
        for case in cases:
            t0 = time.time()
            passed = True
            reason = None
            final_status = "UNKNOWN"
            tools_used = set()
            recovery_attempts = 0
            
            # Fresh memory and orchestrator per test case
            memory = ShortTermMemory()
            orchestrator = Orchestrator(
                planner=self.planner,
                memory=memory,
                executor=self.executor,
                verifier=self.verifier,
                diagnoser=self.diagnoser,
                replanner=self.replanner,
                circuit_breaker=self.circuit_breaker,
                tracer=self.tracer
            )
            
            try:
                # 1 & 2. Submit the user goal
                state = orchestrator.start(case.user_goal)
                
                # Execute all tasks in the generated plan
                executable = orchestrator.get_executable_tasks()
                eval_start = time.time()
                while executable:
                    if time.time() - eval_start > (settings.timeout * 3):
                        passed = False
                        reason = "Evaluation case exceeded maximum global timeout."
                        final_status = "FAILED"
                        break
                        
                    for task in executable:
                        completed_task = orchestrator.run_task_with_recovery(task.task_id)
                        final_status = completed_task.status.value
                    executable = orchestrator.get_executable_tasks()
                    
                duration = time.time() - t0
                
                # 3 & 4. Capture Task state and retrieve trace events
                all_traces = []
                for task_id in state.tasks_state.keys():
                    all_traces.extend(self.tracer.get_traces(task_id))
                    
                # Inspect trace events for metrics
                for t in all_traces:
                    if t.event_type == EventType.TOOL_SELECTED:
                        tool_name = t.metadata.get("tool_name")
                        if tool_name:
                            tools_used.add(tool_name)
                    if t.event_type == EventType.RETRY and t.status == "STARTED":
                        recovery_attempts += 1
                        
                tool_count = len(tools_used)
                
                # 5 & 6. Evaluate Success Criteria & Expected Tools
                
                # Check expected tools
                if passed and case.expected_tools:
                    missing_tools = [t for t in case.expected_tools if t not in tools_used]
                    if missing_tools:
                        passed = False
                        reason = f"Missing expected tools: {missing_tools}"
                        
                # Check final task status
                if passed and final_status != "COMPLETED":
                    passed = False
                    reason = f"Task did not complete successfully. Status: {final_status}"
                    
                # Check deterministic criteria
                if passed and case.success_criteria:
                    if "file_exists" in case.success_criteria:
                        file_path = os.path.join(settings.agent_workspace, case.success_criteria["file_exists"])
                        if not os.path.exists(file_path):
                            passed = False
                            reason = f"Required file does not exist: {case.success_criteria['file_exists']}"
                            
                # Check expected result
                if passed and case.expected_result:
                    found = False
                    for obs in state.observations:
                        if case.expected_result in str(obs.result):
                            found = True
                            break
                    if not found:
                        passed = False
                        reason = f"Expected result '{case.expected_result}' not found in observations."

            except Exception as e:
                passed = False
                reason = f"Exception during execution: {str(e)}"
                duration = time.time() - t0
                tool_count = 0
                
            total_time += duration
            total_tools += tool_count
            total_recoveries += recovery_attempts
            
            # 7 & 8. Produce individual result
            results.append(EvalResult(
                case_id=case.case_id,
                passed=passed,
                failure_reason=reason,
                duration=duration,
                tool_usage_count=tool_count,
                recovery_attempts=recovery_attempts,
                final_task_status=final_status
            ))
            
        passed_cases = sum(1 for r in results if r.passed)
        failed_cases = len(cases) - passed_cases
        
        return EvalReport(
            total_cases=len(cases),
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            success_rate=passed_cases / len(cases) if cases else 0,
            total_duration=total_time,
            average_duration=total_time / len(cases) if cases else 0,
            total_tool_calls=total_tools,
            total_recovery_attempts=total_recoveries,
            results=results
        )
