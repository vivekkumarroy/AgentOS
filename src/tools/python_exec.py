import subprocess
from typing import Any, Dict
from .base import BaseTool
from .schemas import PythonExecutionInput
from ..config import settings

class PythonExecutionTool(BaseTool):
    name = "python_exec"
    description = "Execute Python code in a subprocess. WARNING: Not a secure production sandbox. Runs with host user permissions."
    input_schema = PythonExecutionInput

    def execute(self, code: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            process = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=settings.python_exec_timeout
            )
            
            stdout = process.stdout[:settings.python_max_output]
            stderr = process.stderr[:settings.python_max_output]
            
            if len(process.stdout) > settings.python_max_output:
                stdout += "\n...[Output Truncated]..."
            if len(process.stderr) > settings.python_max_output:
                stderr += "\n...[Output Truncated]..."
                
            status = "SUCCESS" if process.returncode == 0 else "FAILED"
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_status": process.returncode,
                "execution_status": status
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Execution timed out after {settings.python_exec_timeout} seconds.",
                "execution_status": "TIMEOUT"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_status": "ERROR"
            }
