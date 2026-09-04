from typing import List, Dict, Any
import logging
import uuid
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]

class DocumentChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunk_id = str(uuid.uuid4())
                chunk_meta = metadata.copy()
                chunk_meta['chunk_index'] = len(chunks)
                
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    text=chunk_text,
                    metadata=chunk_meta
                ))
            
            start += (self.chunk_size - self.chunk_overlap)
            
            if self.chunk_size - self.chunk_overlap <= 0:
                break
                
        logger.info(f"Chunked document into {len(chunks)} chunks.")
        return chunks
