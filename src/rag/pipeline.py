import os
import logging
from pathlib import Path
from typing import List, Dict, Any
from .document_loader import DocumentLoader
from .chunker import DocumentChunker
from .retriever import Retriever
from ..memory.long_term import VectorStore

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, 
                 vector_store: VectorStore, 
                 workspace: str,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        self.vector_store = vector_store
        self.loader = DocumentLoader(workspace)
        self.chunker = DocumentChunker(chunk_size, chunk_overlap)
        self.retriever = Retriever(vector_store)

    def ingest_document(self, file_path: str) -> int:
        logger.info(f"Ingesting document: {file_path}")
        doc = self.loader.load_document(file_path)
        chunks = self.chunker.chunk_document(doc['text'], doc['metadata'])
        
        if not chunks:
            logger.warning(f"No text found to chunk in {file_path}")
            return 0
            
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metas = [c.metadata for c in chunks]
        
        self.vector_store.add_documents(ids=ids, texts=texts, metadatas=metas)
        logger.info(f"Successfully ingested {len(chunks)} chunks for {file_path}")
        return len(chunks)

    def ingest_directory(self, dir_path: str) -> int:
        path = Path(dir_path).resolve()
        if not path.is_dir():
            raise NotADirectoryError(f"{dir_path} is not a directory.")
            
        # Quick validation
        self.loader._validate_path(str(path))
        
        total_chunks = 0
        for root, _, files in os.walk(path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in ['.txt', '.md', '.pdf']:
                    try:
                        total_chunks += self.ingest_document(os.path.join(root, file))
                    except Exception as e:
                        logger.error(f"Failed to ingest {file}: {e}")
                        
        return total_chunks

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.retriever.retrieve(query, top_k)
