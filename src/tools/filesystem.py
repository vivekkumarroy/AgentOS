import os
from typing import Any, Dict
from pathlib import Path
from .base import BaseTool
from .schemas import ReadFileInput, WriteFileInput, ListDirectoryInput, SearchFilesInput
from ..config import settings

def _resolve_and_validate_path(target_path: str) -> Path:
    """Resolves path and ensures it stays within the configured AGENT_WORKSPACE."""
    workspace = Path(settings.agent_workspace).resolve()
    # Ensure workspace exists
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Path(target_path).resolve() handles '..', '..\\', mixed slashes, etc.
    # However, if target_path is absolute (e.g. C:\Windows), Path(target_path) ignores the workspace.
    
    # We first join the paths without resolving, in case it's absolute, Path will just take the absolute.
    raw_path = Path(target_path)
    if raw_path.is_absolute():
        full_target = raw_path.resolve()
    else:
        full_target = (workspace / target_path).resolve()
    
    try:
        # Check if the resolved path is relative to the workspace.
        full_target.relative_to(workspace)
    except ValueError:
        raise ValueError(f"Access denied: path '{target_path}' is outside the workspace.")
    
    return full_target

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file."
    input_schema = ReadFileInput

    def execute(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            safe_path = _resolve_and_validate_path(path)
            if not safe_path.is_file():
                return {"success": False, "error": f"File not found: {path}"}
            
            content = safe_path.read_text(encoding="utf-8")
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file."
    input_schema = WriteFileInput

    def execute(self, path: str, content: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            safe_path = _resolve_and_validate_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding="utf-8")
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and directories in a path."
    input_schema = ListDirectoryInput

    def execute(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            safe_path = _resolve_and_validate_path(path)
            if not safe_path.is_dir():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            items = [item.name for item in safe_path.iterdir()]
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for a term in files within a directory."
    input_schema = SearchFilesInput

    def execute(self, directory: str, search_term: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            safe_path = _resolve_and_validate_path(directory)
            if not safe_path.is_dir():
                return {"success": False, "error": f"Directory not found: {directory}"}
            
            matches = []
            for file_path in safe_path.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if search_term in content:
                            matches.append(str(file_path.relative_to(safe_path)))
                    except UnicodeDecodeError:
                        pass
            
            return {"success": True, "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}
