from src.rag.chunker import DocumentChunker

def test_document_chunker():
    chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
    text = "0123456789abcdefghij" # 20 chars
    chunks = chunker.chunk_document(text, {"source": "test"})
    
    # 0-10, 8-18, 16-26 (only up to 20)
    assert len(chunks) == 3
    assert chunks[0].text == "0123456789"
    assert chunks[1].text == "89abcdefgh"
    assert chunks[2].text == "ghij"
    
    assert chunks[0].metadata["source"] == "test"
    assert chunks[0].metadata["chunk_index"] == 0
