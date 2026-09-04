from src.memory.embeddings import get_embedding_provider, ChromaDefaultEmbedding

def test_chroma_default_embedding():
    provider = ChromaDefaultEmbedding()
    text = "Hello world"
    vec = provider.embed_text(text)
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert isinstance(vec[0], float)
    
    vecs = provider.embed_documents(["Hello", "World"])
    assert isinstance(vecs, list)
    assert len(vecs) == 2
