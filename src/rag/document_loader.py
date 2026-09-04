import os
import logging
from typing import Dict, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self, allowed_workspace: str):
        self.allowed_workspace = Path(allowed_workspace).resolve()

    def _validate_path(self, file_path: str) -> Path:
        path = Path(file_path).resolve()
        try:
            path.relative_to(self.allowed_workspace)
        except ValueError:
            raise PermissionError(f"Access to path '{file_path}' is denied. Outside allowed workspace.")
        if not path.exists():
             # We might be validating a directory so don't fail immediately on is_file if it's a dir validation,
             # but this is mostly for files. Let the caller check is_dir if needed.
             pass
        return path

    def load_document(self, file_path: str) -> Dict[str, Any]:
        path = self._validate_path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File '{file_path}' not found.")
            
        ext = path.suffix.lower()
        
        metadata = {
            "source": str(path),
            "filename": path.name,
            "document_type": ext,
            "ingestion_timestamp": time.time()
        }
        
        if ext in ['.txt', '.md']:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            return {"text": text, "metadata": metadata}
            
        elif ext == '.pdf':
            try:
                import pypdf
            except ImportError:
                raise ImportError("pypdf is required to read PDF files.")
                
            text_parts = []
            with open(path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            text = "\n\n".join(text_parts)
            return {"text": text, "metadata": metadata}
        else:
            raise ValueError(f"Unsupported document type: {ext}")
