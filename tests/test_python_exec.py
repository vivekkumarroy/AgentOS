from src.tools.python_exec import PythonExecutionTool

def test_python_exec_success():
    tool = PythonExecutionTool()
    res = tool.execute("print('hello')")
    assert res["success"] is True
    assert res["stdout"].strip() == "hello"
    assert res["execution_status"] == "SUCCESS"

def test_python_exec_syntax_error():
    tool = PythonExecutionTool()
    res = tool.execute("print('hello'")
    assert res["success"] is False
    assert "SyntaxError" in res["stderr"]
    assert res["execution_status"] == "FAILED"

def test_python_exec_timeout(monkeypatch):
    from src.config import settings
    monkeypatch.setattr(settings, "python_exec_timeout", 1)
    tool = PythonExecutionTool()
    res = tool.execute("import time; time.sleep(2)")
    assert res["success"] is False
    assert res["execution_status"] == "TIMEOUT"
