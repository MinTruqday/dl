import asyncio
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from rank_bm25 import BM25Okapi

from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.schemas.memory import MemoryItem, MemoryOperation
from src.memory.management import memory_manager

class MemoryManager:
    """
    <module_purpose>
    <purpose>Custom Memory Engine acting as a drop-in replacement for mem0ai (Deep Core with BM25 Hybrid).</purpose>
    <metis_behavior>Extracts long-term semantic, episodic, and procedural memory directly to Qdrant without external dependencies. Features Hash Deduplication, Multi-tenant filtering, Redis history tracking, and BM25 Semantic Re-ranking.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self.collection_name = "doclib_memories"
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            timeout=10.0,
        )
        self._hf = HuggingFaceEndpoint(
            repo_id=settings.LLM_MODEL,
            huggingfacehub_api_token=settings.HF_TOKEN,
            temperature=0.1,
            task="conversational",
        )
        self.llm = ChatHuggingFace(llm=self._hf)
        self._init_task = asyncio.create_task(self._ensure_collection())
        from src.rag.embedding import embedder
        self.embedder = embedder

    async def _ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedder._dimensions, distance=Distance.COSINE
                    ),
                )
        except Exception:
            logger.exception("Memory collection initialization error")

    async def search_and_resolve_conflicts(self, new_content: str, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> Optional[MemoryOperation]:
        existing = await self.search(new_content, user_id, agent_id, run_id)
        if not existing:
            return None
            
        existing_text = "\n".join([f"ID: {m.get('id', 'N/A')} - {m.get('text', '')}" for m in existing])
        prompt = f"""You are a memory manager. A new fact has been extracted: "{new_content}".
Existing memories:
{existing_text}

Determine if this new fact conflicts with, updates, or supersedes any existing memory.
Return JSON mapping to MemoryOperation schema with 'add', 'update', or 'delete' lists."""

        try:
            structured_llm = self.llm.with_structured_output(MemoryOperation)
            msg = [SystemMessage(content=prompt), HumanMessage(content="Analyze and resolve conflicts.")]
            return await structured_llm.ainvoke(msg)
        except Exception as e:
            logger.exception(f"Conflict resolution failed for user '{user_id}'. Error: {str(e)}")
            return MemoryOperation()

    async def _extract_operations(self, messages: List[Dict], memory_scope: str = "user") -> MemoryOperation:
        prompt_type = PromptType.MEMORY_EXTRACTION if memory_scope == "user" else PromptType.AGENT_MEMORY_EXTRACTION
        system_prompt = registry.get(prompt_type)
        chat_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        try:
            structured_llm = self.llm.with_structured_output(MemoryOperation)
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=chat_text)]
            return await structured_llm.ainvoke(msg)
        except Exception as e:
            logger.exception(f"Memory extraction execution failed. Input length: {len(messages)} messages. Error: {str(e)}")
            return MemoryOperation()

    def _build_filter(self, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> Filter:
        conditions = [FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        if agent_id:
            conditions.append(FieldCondition(key="agent_id", match=MatchValue(value=agent_id)))
        if run_id:
            conditions.append(FieldCondition(key="run_id", match=MatchValue(value=run_id)))
            
        current_time = datetime.now(timezone.utc).isoformat()
        conditions.append(
            FieldCondition(
                key="expires_at", 
                match=MatchValue(value=""), 
                # Simplistic way to represent null/none or handle expiration logic in Qdrant
                # For robust TTL, we should just filter out in Python or use Range condition if stored as timestamp.
                # Let's handle expiration filtering in python for simplicity if Qdrant schema isn't strictly typed.
            )
        ) # We'll do post-filtering for TTL to avoid Qdrant strict index errors.
        return Filter(must=conditions)

    async def add(self, messages: List[Dict], user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None, memory_scope: str = "user"):
        if not user_id or user_id == "guess_user":
            user_id = "default"
            
        await self._ensure_collection()
        operations = await self._extract_operations(messages, memory_scope=memory_scope)
        points = []
        
        existing_hashes = set()
        try:
            scroll_filter = self._build_filter(user_id, agent_id, run_id)
            records, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=1000,
                with_payload=True
            )
            for r in records:
                if 'hash' in r.payload:
                    existing_hashes.add(r.payload['hash'])
        except Exception:
            logger.exception("Hash deduplication pre-fetch error")

        for item in operations.add:
            content_hash = hashlib.md5(item.content.encode('utf-8')).hexdigest()
            if content_hash in existing_hashes:
                logger.info(f"Memory skipped due to exact hash match: {content_hash}")
                continue
                
            resolved_ops = await self.search_and_resolve_conflicts(item.content, user_id, agent_id, run_id)
            if resolved_ops:
                operations.add.extend([m for m in resolved_ops.add if m.content != item.content])
                operations.update.extend(resolved_ops.update)
                operations.delete.extend(resolved_ops.delete)
                if not any(m.content == item.content for m in resolved_ops.add):
                    continue
                
            item_id = str(uuid.uuid4())
            try:
                vector = await asyncio.to_thread(self.embedder.embed_query, item.content)
                payload = {
                    "text": item.content,
                    "category": getattr(item, "category", "fact"),
                    "memory_type": getattr(item, "memory_type", "semantic"),
                    "user_id": user_id,
                    "hash": content_hash,
                    "agent_id": agent_id,
                    "run_id": run_id,
                    "expires_at": getattr(item, "expires_at", None),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                points.append(PointStruct(id=item_id, vector=vector, payload=payload))
                asyncio.create_task(memory_manager.save_memory_history(item_id, "ADD", None, item.content))
            except Exception as e:
                logger.exception(f"Failed to generate embedding or create PointStruct for memory. Content hash: {content_hash}. Error: {str(e)}")

        if points:
            try:
                await self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info(f"Successfully upserted {len(points)} memory points for user_id='{user_id}', agent_id='{agent_id}'. MD5 Dedup skipped {len(existing_hashes)} items.")
                
                for p in points:
                    if p.payload.get("memory_type") == "entity":
                        edge_data = json.dumps({"source_id": p.id, "text": p.payload.get("text"), "created_at": p.payload.get("created_at")})
                        await memory_manager._redis.sadd(f"entity:graph:{user_id}:edges", edge_data)
            except Exception as e:
                logger.exception(f"Failed to upsert memory points into Qdrant collection '{self.collection_name}'. Error: {str(e)}")
                
        for item in operations.update:
            if item.id:
                await self.update(item.id, item.content)
                
        for del_id in operations.delete:
            await self.delete(del_id)

    add_memory = add

    async def get(self, memory_id: str) -> Optional[Dict]:
        try:
            res = await self.client.retrieve(self.collection_name, ids=[memory_id])
            if res:
                return res[0].payload
        except Exception:
            logger.exception("Memory get error")
        return None

    async def get_all(self, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict]:
        try:
            query_filter = self._build_filter(user_id, agent_id, run_id)
            if filters:
                for k, v in filters.items():
                    query_filter.must.append(FieldCondition(key=k, match=MatchValue(value=v)))
                    
            records, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            return [r.payload for r in records if r.payload and not self._is_expired(r.payload)]
        except Exception as e:
            logger.exception(f"Failed to execute get_all for user_id='{user_id}'. Error: {str(e)}")
            return []

    def _is_expired(self, payload: Dict) -> bool:
        expires_at = payload.get("expires_at")
        if not expires_at:
            return False
        try:
            exp = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) > exp
        except:
            return False

    async def search(self, query: str, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        if not user_id or user_id == "guess_user":
            return []
            
        try:
            query_filter = self._build_filter(user_id, agent_id, run_id)
            if filters:
                for k, v in filters.items():
                    query_filter.must.append(FieldCondition(key=k, match=MatchValue(value=v)))
                    
            vector = await asyncio.to_thread(self.embedder.embed_query, query)
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter,
                limit=limit * 2,
                with_payload=True
            )

            if not results:
                return []

            memories = []
            for r in results:
                payload = r.payload if hasattr(r, 'payload') else r.get('payload', {})
                if 'text' in payload and not self._is_expired(payload):
                    memories.append(payload)

            if not memories:
                return []

            if len(memories) > 1:
                tokenized_corpus = [doc.get("text", "").lower().split(" ") for doc in memories]
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = query.lower().split(" ")
                doc_scores = bm25.get_scores(tokenized_query)
                scored_memories = []
                for i, mem in enumerate(memories):
                    semantic_score = len(memories) - i
                    hybrid_score = semantic_score + doc_scores[i]
                    scored_memories.append((hybrid_score, mem))
                
                scored_memories.sort(key=lambda x: x[0], reverse=True)
                memories = [m for _, m in sorted(scored_memories, reverse=True, key=lambda x: x[0])]

            if len(memories) > limit:
                memories = memories[:limit]

            return memories
        except Exception as e:
            logger.exception(f"Failed to execute search for query '{query}' and user_id '{user_id}'. Error: {str(e)}")
            return []

    async def get_memories(self, user_id: str, query: str = None, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> str:
        if query:
            results = await self.search(query, user_id, agent_id, run_id)
        else:
            results = await self.get_all(user_id, agent_id, run_id, limit=5)
            
        if not results:
            return ""
            
        memories = [m.get("text") for m in results if m.get("text")]
        if not memories:
            return ""
            
        formatted = "\n".join([f"- {m}" for m in memories])
        return f"Relevant Long-term Context:\n{formatted}\n"

    async def update(self, memory_id: str, new_content: str):
        try:
            vector = await asyncio.to_thread(self.embedder.embed_query, new_content)
            res = await self.client.retrieve(self.collection_name, ids=[memory_id])
            if res:
                payload = res[0].payload
                old_content = payload.get("text")
                payload["text"] = new_content
                payload["hash"] = hashlib.md5(new_content.encode('utf-8')).hexdigest()
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=[PointStruct(id=memory_id, vector=vector, payload=payload)]
                )
                asyncio.create_task(memory_manager.save_memory_history(memory_id, "UPDATE", old_content, new_content))
                logger.info(f"Successfully updated memory '{memory_id}' with new content.")
        except Exception as e:
            logger.exception(f"Failed to update memory '{memory_id}'. Error: {str(e)}")
            
    update_memory = update

    async def delete(self, memory_id: str):
        try:
            res = await self.client.retrieve(self.collection_name, ids=[memory_id])
            if res:
                old_content = res[0].payload.get("text")
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=[memory_id]
                )
                asyncio.create_task(memory_manager.save_memory_history(memory_id, "DELETE", old_content, None))
                logger.info(f"Successfully deleted memory '{memory_id}'.")
        except Exception as e:
            logger.exception(f"Failed to delete memory '{memory_id}'. Error: {str(e)}")
            
    delete_memory = delete
    
    async def delete_all(self, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None, filters: Optional[Dict] = None):
        try:
            query_filter = self._build_filter(user_id, agent_id, run_id)
            if filters:
                for k, v in filters.items():
                    query_filter.must.append(FieldCondition(key=k, match=MatchValue(value=v)))
                    
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=query_filter.must)
            )
            logger.info(f"Successfully executed bulk delete_all for user_id='{user_id}', agent_id='{agent_id}'.")
        except Exception as e:
            logger.exception(f"Failed to execute bulk delete_all. Error: {str(e)}")

    async def history(self, memory_id: str) -> List[Dict]:
        try:
            key = f"memory:history:{memory_id}"
            if memory_manager._redis:
                import json
                existing = await memory_manager._redis.get(key)
                if existing:
                    return json.loads(existing)
            return []
        except Exception:
            logger.exception("Memory history read error")
            return []

    async def get_context(self, query: str, user_id: str) -> str:
        return await self.get_memories(user_id, query)

    async def reset(self):
        try:
            await self.client.delete_collection(self.collection_name)
            logger.info("Successfully reset entire memory collection.")
        except Exception as e:
            logger.exception(f"Failed to reset memory collection. Error: {str(e)}")

    async def close(self):
        try:
            if hasattr(self.client, 'close'):
                await self.client.close()
            logger.info("Successfully closed memory client.")
        except Exception as e:
            logger.exception(f"Failed to close memory client. Error: {str(e)}")

mem0_manager = MemoryManager()
