from abc import ABC, abstractmethod
from typing import List
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

class ChromaDefaultEmbedding(EmbeddingProvider):
    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self.ef = DefaultEmbeddingFunction()
        
    def embed_text(self, text: str) -> List[float]:
        res = self.ef([text])[0]
        return res.tolist() if hasattr(res, 'tolist') else list(res)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        res = self.ef(texts)
        return [r.tolist() if hasattr(r, 'tolist') else list(r) for r in res]

def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_model.lower() == "local":
        return ChromaDefaultEmbedding()
    else:
        logger.warning(f"Embedding model '{settings.embedding_model}' requested, but only 'local' is fully configured. Defaulting to local.")
        return ChromaDefaultEmbedding()
