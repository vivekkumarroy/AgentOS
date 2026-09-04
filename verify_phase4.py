import os
import sys
from src.api import long_term_memory, rag_pipeline
from src.config import settings

def verify():
    print("--- VERIFYING PHASE 4 ---")
    
    # 1. Document ingestion and semantic retrieval
    workspace = settings.agent_workspace
    os.makedirs(workspace, exist_ok=True)
    test_doc = os.path.join(workspace, "test_ingestion.txt")
    with open(test_doc, "w", encoding="utf-8") as f:
        f.write("AgentOS is a powerful autonomous framework. Phase 4 introduces long-term memory via ChromaDB and semantic RAG.")
    
    print(f"Ingesting document: {test_doc}")
    chunks = rag_pipeline.ingest_document(test_doc)
    print(f"Chunks created: {chunks}")
    
    print("Retrieving context for 'autonomous framework'...")
    res = rag_pipeline.retrieve("autonomous framework", top_k=1)
    for r in res:
        print(f"Result: {r['text']}")

    # 2. Workspace path security
    print("\n--- VERIFYING PATH SECURITY ---")
    try:
        rag_pipeline.ingest_document("../../outside_doc.txt")
        print("FAIL: Path security bypassed!")
    except PermissionError as e:
        print(f"PASS: Path traversal blocked - {e}")

    # 3. Persistence Verification
    print("\n--- VERIFYING PERSISTENCE ---")
    # Store directly in long_term_memory
    rec = long_term_memory.store_memory("This is a persistent test memory.", {"type": "verification"})
    print(f"Stored memory ID: {rec.memory_id}")
    count_before = long_term_memory.count_memories()
    print(f"Total memories in DB: {count_before}")
    
if __name__ == "__main__":
    verify()
