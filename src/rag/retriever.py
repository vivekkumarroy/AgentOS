import logging
from typing import List, Dict, Any
from ..memory.long_term import VectorStore

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving top {top_k} chunks for query: '{query}'")
        results = self.vector_store.search_documents(query, top_k)
        
        if not results:
            logger.info("No relevant documents found.")
            return []
            
        results.sort(key=lambda x: x.get('distance', float('inf')))
        return results
