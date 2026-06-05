import asyncio
from src.store.vector_store import vector_store
from src.agents.knowledge import KnowledgeAgent

async def main():
    doc_id = "019e92c3-9f02-792a-a307-3ecf552ade16"
    
    # 1. Check if vector store has data
    await vector_store.ensure_collection()
    info = await vector_store.client.get_collection(vector_store.collection_name)
    print("Vector Store Collection Count:", info.points_count)
    
    # 2. Search for chunking or generic terms
    results = await vector_store.query([0.0]*768, document_id=doc_id, limit=3)
    print(f"Found {len(results)} chunks for doc {doc_id}")
    for r in results:
        print("-", r["metadata"].get("text", "")[:100])

if __name__ == "__main__":
    asyncio.run(main())
