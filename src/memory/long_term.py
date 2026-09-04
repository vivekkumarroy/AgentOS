from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import uuid
import time
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MemoryRecord(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def delete_documents(self, ids: List[str]):
        pass

    @abstractmethod
    def search_documents(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def count_documents(self) -> int:
        pass

    @abstractmethod
    def clear_collection(self):
        pass

class ChromaVectorStore(VectorStore):
    def __init__(self, db_path: str, collection_name: str, embedding_function=None):
        import chromadb
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Determine the actual embedding function to pass to chromadb
        if embedding_function:
            # We wrap our provider in Chroma's expected interface
            from chromadb import EmbeddingFunction
            
            class CustomEmbeddingFunction(EmbeddingFunction):
                def __init__(self, ef):
                    self.ef = ef
                def __call__(self, input: List[str]) -> List[List[float]]:
                    return self.ef.embed_documents(input)
                def name(self) -> str:
                    return "custom_embedding_function"
            
            ef_chroma = CustomEmbeddingFunction(embedding_function)
        else:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            ef_chroma = DefaultEmbeddingFunction()
            
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=ef_chroma
        )

    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        self.collection.add(ids=ids, documents=texts, metadatas=metadatas)

    def delete_documents(self, ids: List[str]):
        if ids:
            self.collection.delete(ids=ids)

    def search_documents(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        formatted = []
        if not results['ids'] or not results['ids'][0]:
            return formatted
            
        for i in range(len(results['ids'][0])):
            formatted.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
            })
        return formatted

    def count_documents(self) -> int:
        return self.collection.count()

    def clear_collection(self):
        count = self.collection.count()
        if count > 0:
            all_data = self.collection.get()
            if all_data['ids']:
                self.collection.delete(ids=all_data['ids'])

class LongTermMemory:
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store

    def store_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryRecord:
        record = MemoryRecord(text=text, metadata=metadata or {})
        record.metadata['created_at'] = record.created_at
        
        self.store.add_documents(
            ids=[record.memory_id],
            texts=[record.text],
            metadatas=[record.metadata]
        )
        logger.info(f"Stored long-term memory with id: {record.memory_id}")
        return record

    def retrieve_memories(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving memories for query: {query}")
        return self.store.search_documents(query, top_k)

    def delete_memory(self, memory_id: str):
        logger.info(f"Deleting memory with id: {memory_id}")
        self.store.delete_documents([memory_id])

    def clear_memory(self):
        logger.warning("Clearing all long-term memory")
        self.store.clear_collection()

    def count_memories(self) -> int:
        return self.store.count_documents()
