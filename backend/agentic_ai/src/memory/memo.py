import asyncio
import hashlib
import math
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid6 import uuid7

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, Range, VectorParams, MatchAny, MatchExcept
from rank_bm25 import BM25Okapi

from src.core.infrastructure.configuration import settings
from src.utils.background import create_background_task
from src.utils.huggingface import create_chat_model
from src.core.registry import PromptType, registry
from src.schemas.memory import MemoryOperation
from src.memory.management import memory_manager

class EntityStore:
    def __init__(self, memory_manager_ref):
        self.mm = memory_manager_ref

    async def _upsert_entity(self, entity_text: str, entity_type: str, memory_id: str, user_id: str):
        try:
            if not memory_manager._redis:
                return
            edge_data = json.dumps({"source_id": memory_id, "text": entity_text, "type": entity_type, "created_at": datetime.now(timezone.utc).isoformat()})
            await memory_manager._redis.sadd(f"entity:graph:{user_id}:edges", edge_data)
            logger.info("Memory entity upserted type={}", entity_type)
        except Exception:
            logger.exception("Memory entity upsert failed")

    async def _link_entities_for_memory(self, memory_id: str, text: str, user_id: str):
        system_prompt = registry.get(PromptType.GRAPHRAG_ENTITY_EXTRACTION)
        try:
            from pydantic import BaseModel, Field
            class EntityRelation(BaseModel):
                source: str = Field(description="Source entity name")
                relation: str = Field(description="Action or relationship verb")
                target: str = Field(description="Target entity name")
            class ExtractedGraph(BaseModel):
                relations: List[EntityRelation]

            structured_llm = self.mm.llm.with_structured_output(ExtractedGraph)
            res = await structured_llm.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=text)])
            for rel in res.relations:
                await self._upsert_entity(rel.source, rel.relation, memory_id, user_id)
                await self._upsert_entity(rel.target, "TARGET_NODE", memory_id, user_id)
        except Exception:
            logger.exception("Memory entity extraction failed")

    async def search(self, query: str, user_id: str) -> List[Dict]:
        return await self.search_graph(query, user_id)

    async def search_graph(self, query: str, user_id: str) -> List[Dict]:
        try:
            if not memory_manager._redis:
                return []
            edges = await memory_manager._redis.smembers(f"entity:graph:{user_id}:edges")
            results = []
            for e in edges:
                data = json.loads(e)
                if query.lower() in data.get("text", "").lower():
                    results.append(data)
            return results
        except Exception:
            logger.exception("Memory entity graph search failed")
            return []

    async def get_graph(self, user_id: str) -> Dict[str, Any]:
        try:
            if not memory_manager._redis:
                return {"user_id": user_id, "nodes": [], "edges": []}
            edges = await memory_manager._redis.smembers(f"entity:graph:{user_id}:edges")
            parsed_edges = [json.loads(e) for e in edges]
            nodes = list({e.get("text") for e in parsed_edges if e.get("text")})
            return {"user_id": user_id, "nodes": nodes, "edges": parsed_edges}
        except Exception:
            logger.exception("Memory entity graph read failed")
            return {"user_id": user_id, "nodes": [], "edges": []}

    async def delete_graph(self, user_id: str, entity_name: Optional[str] = None) -> bool:
        try:
            if not memory_manager._redis:
                return True
            key = f"entity:graph:{user_id}:edges"
            if not entity_name:
                await memory_manager._redis.delete(key)
                logger.info("Memory entity graph deleted")
                return True

            edges = await memory_manager._redis.smembers(key)
            for e in edges:
                data = json.loads(e)
                if data.get("text") == entity_name:
                    await memory_manager._redis.srem(key, e)
            logger.info("Memory graph entity deleted")
            return True
        except Exception:
            logger.exception("Memory entity graph delete failed")
            return False

class ProjectStore:
    def __init__(self, memory_manager_ref):
        self.mm = memory_manager_ref

    async def get_project(self, project_id: str) -> Optional[Dict]:
        try:
            if not memory_manager._redis:
                return None
            data = await memory_manager._redis.get(f"project:{project_id}")
            return json.loads(data) if data else None
        except Exception:
            logger.exception("Memory project read failed")
            return None

    async def add_project(self, project_id: str, name: str, org_id: str):
        try:
            if not memory_manager._redis:
                return
            data = json.dumps({"id": project_id, "name": name, "org_id": org_id})
            await memory_manager._redis.set(f"project:{project_id}", data)
        except Exception:
            logger.exception("Memory project write failed")

class MemoryManager:
    def __init__(self):
        self.collection_name = "doclib_memories"
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            timeout=10.0,
        )
        self.llm = create_chat_model()
        from src.rag.embedding import embedder
        self.embedder = embedder
        self._initialized = False
        self._init_lock = None
        self._entity_store = EntityStore(self)
        self._project_store = ProjectStore(self)

    async def _ensure_collection(self):
        if self._initialized:
            return
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        async with self._init_lock:
            if self._initialized:
                return
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
                self._initialized = True
            except Exception:
                logger.exception("Memory collection initialization failed")

    def _calculate_recency_score(self, created_at_iso: str, decay_rate: float = 0.01) -> float:
        try:
            created_at = datetime.fromisoformat(created_at_iso.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta_days = (now - created_at).total_seconds() / 86400.0
            return math.exp(-decay_rate * max(0.0, delta_days))
        except Exception:
            return 1.0

    async def search_and_resolve_conflicts(self, new_content: str, user_id: str, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> Optional[MemoryOperation]:
        existing = await self.search(new_content, user_id=user_id, agent_id=agent_id, run_id=run_id)
        if not existing:
            return None

        existing_text = "\n".join([f"ID: {m.get('id', 'N/A')} - {m.get('text', '')}" for m in existing])
        prompt = registry.get(PromptType.MEMORY_CONFLICT_RESOLUTION).format(new_content=new_content, existing_text=existing_text)

        try:
            structured_llm = self.llm.with_structured_output(MemoryOperation)
            msg = [SystemMessage(content=prompt), HumanMessage(content="Analyze and resolve conflicts.")]
            return await structured_llm.ainvoke(msg)
        except Exception:
            logger.exception("Memory conflict resolution failed")
            return MemoryOperation()

    async def _extract_operations(self, messages: List[Dict], memory_scope: str = "user") -> MemoryOperation:
        prompt_type = PromptType.MEMORY_EXTRACTION if memory_scope == "user" else PromptType.AGENT_MEMORY_EXTRACTION
        system_prompt = registry.get(prompt_type)
        chat_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        try:
            structured_llm = self.llm.with_structured_output(MemoryOperation)
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=chat_text)]
            return await structured_llm.ainvoke(msg)
        except Exception:
            logger.exception("Memory extraction failed message_count={}", len(messages))
            return MemoryOperation()

    def _build_filter(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Filter:
        conditions = []
        if user_id:
            conditions.append(FieldCondition(key="user_id", match=MatchValue(value=user_id)))
        if agent_id:
            conditions.append(FieldCondition(key="agent_id", match=MatchValue(value=agent_id)))
        if run_id:
            conditions.append(FieldCondition(key="run_id", match=MatchValue(value=run_id)))
        if org_id:
            conditions.append(FieldCondition(key="org_id", match=MatchValue(value=org_id)))
        if project_id:
            conditions.append(FieldCondition(key="project_id", match=MatchValue(value=project_id)))
        if category:
            conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))

        if filters:
            for k, v in filters.items():
                if isinstance(v, dict):
                    if "$gt" in v:
                        conditions.append(FieldCondition(key=k, range=Range(gt=v["$gt"])))
                    elif "$lt" in v:
                        conditions.append(FieldCondition(key=k, range=Range(lt=v["$lt"])))
                    elif "$gte" in v:
                        conditions.append(FieldCondition(key=k, range=Range(gte=v["$gte"])))
                    elif "$lte" in v:
                        conditions.append(FieldCondition(key=k, range=Range(lte=v["$lte"])))
                    elif "$in" in v and isinstance(v["$in"], list):
                        conditions.append(FieldCondition(key=k, match=MatchAny(any=v["$in"])))
                    elif "$nin" in v and isinstance(v["$nin"], list):
                        conditions.append(FieldCondition(key=k, match=MatchExcept(except_=v["$nin"])))
                else:
                    conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))

        return Filter(must=conditions)

    async def users(self) -> List[str]:
        try:
            await self._ensure_collection()
            records, _ = await self.client.scroll(collection_name=self.collection_name, limit=1000, with_payload=True)
            user_set = {r.payload.get("user_id") for r in records if r.payload and r.payload.get("user_id")}
            return sorted(list(user_set))
        except Exception:
            logger.exception("Memory user listing failed")
            return []

    async def agents(self) -> List[str]:
        try:
            await self._ensure_collection()
            records, _ = await self.client.scroll(collection_name=self.collection_name, limit=1000, with_payload=True)
            agent_set = {r.payload.get("agent_id") for r in records if r.payload and r.payload.get("agent_id")}
            return sorted(list(agent_set))
        except Exception:
            logger.exception("Memory agent listing failed")
            return []

    async def runs(self) -> List[str]:
        try:
            await self._ensure_collection()
            records, _ = await self.client.scroll(collection_name=self.collection_name, limit=1000, with_payload=True)
            run_set = {r.payload.get("run_id") for r in records if r.payload and r.payload.get("run_id")}
            return sorted(list(run_set))
        except Exception:
            logger.exception("Memory run listing failed")
            return []

    async def _create_procedural_memory(self, messages: List[Dict]) -> MemoryOperation:
        prompt_type = PromptType.AGENT_MEMORY_EXTRACTION
        system_prompt = registry.get(prompt_type)
        system_prompt += "\nExtract ONLY procedural lessons and systemic instructions (code snippets, error workarounds). Set memory_type to 'procedural'."
        chat_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        try:
            structured_llm = self.llm.with_structured_output(MemoryOperation)
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=chat_text)]
            return await structured_llm.ainvoke(msg)
        except Exception:
            logger.exception("Procedural memory extraction failed")
            return MemoryOperation()

    async def add(
        self,
        messages: List[Dict],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        memory_scope: str = "user"
    ):
        if not user_id and not org_id and not project_id:
            user_id = "default"

        await self._ensure_collection()
        operations = await self._extract_operations(messages, memory_scope=memory_scope)
        if memory_scope == "agent":
            proc_ops = await self._create_procedural_memory(messages)
            operations.add.extend(proc_ops.add)
            operations.update.extend(proc_ops.update)
            operations.delete.extend(proc_ops.delete)

        points = []
        existing_hashes = set()
        try:
            scroll_filter = self._build_filter(user_id=user_id, agent_id=agent_id, run_id=run_id)
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
            content_hash = hashlib.sha256(item.content.encode('utf-8')).hexdigest()
            if content_hash in existing_hashes:
                logger.info(f"Memory skipped due to exact hash match: {content_hash}")
                continue

            resolved_ops = await self.search_and_resolve_conflicts(item.content, user_id=user_id, agent_id=agent_id, run_id=run_id)
            if resolved_ops:
                operations.add.extend([m for m in resolved_ops.add if m.content != item.content])
                operations.update.extend(resolved_ops.update)
                operations.delete.extend(resolved_ops.delete)
                if not any(m.content == item.content for m in resolved_ops.add):
                    continue

            item_id = str(uuid7())
            try:
                vector = await self.embedder.embed_query(item.content)
                item_cat = category or getattr(item, "category", "user_preference")
                payload = {
                    "text": item.content,
                    "category": item_cat if item_cat else "user_preference",
                    "memory_type": getattr(item, "memory_type", "semantic") if getattr(item, "memory_type", "semantic") else "semantic",
                    "user_id": user_id or "",
                    "org_id": org_id or "",
                    "project_id": project_id or "",
                    "hash": content_hash,
                    "agent_id": agent_id or "",
                    "run_id": run_id or "",
                    "expires_at": getattr(item, "expires_at", None),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                points.append(PointStruct(id=item_id, vector=vector, payload=payload))
                create_background_task(
                    memory_manager.save_memory_history(
                        item_id,
                        "ADD",
                        None,
                        item.content,
                    ),
                    f"memory-history-add-{item_id}",
                )
                if user_id:
                    create_background_task(
                        self._entity_store._link_entities_for_memory(
                            item_id,
                            item.content,
                            user_id,
                        ),
                        f"memory-entity-link-{item_id}",
                    )
            except Exception:
                logger.exception("Memory embedding generation failed")

        if points:
            try:
                await self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info("Memory points upserted count={}", len(points))
                for p in points:
                    if p.payload.get("memory_type") == "entity":
                        edge_data = json.dumps({"source_id": p.id, "text": p.payload.get("text"), "created_at": p.payload.get("created_at")})
                        if memory_manager._redis:
                            await memory_manager._redis.sadd(f"entity:graph:{user_id}:edges", edge_data)
            except Exception:
                logger.exception("Memory point upsert failed")

        for item in operations.update:
            if item.id:
                await self.update(item.id, item.content)

        for del_id in operations.delete:
            await self.delete(del_id)

    add_memory = add

    async def batch_add(self, batch_items: List[Dict[str, Any]]):
        tasks = []
        for item in batch_items:
            messages = item.get("messages", [])
            user_id = item.get("user_id")
            agent_id = item.get("agent_id")
            run_id = item.get("run_id")
            org_id = item.get("org_id")
            project_id = item.get("project_id")
            category = item.get("category")
            memory_scope = item.get("memory_scope", "user")
            tasks.append(self.add(messages, user_id, agent_id, run_id, org_id, project_id, category, memory_scope))
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Completed batch_add for {len(batch_items)} memory items")

    async def batch_update(self, updates: List[Dict[str, str]]):
        tasks = [self.update(u["id"], u["content"]) for u in updates if "id" in u and "content" in u]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Completed batch_update for {len(updates)} memory items")

    async def batch_delete(self, memory_ids: List[str]):
        tasks = [self.delete(mid) for mid in memory_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Completed batch_delete for {len(memory_ids)} memory items")

    async def get(self, memory_id: str) -> Optional[Dict]:
        await self._ensure_collection()
        try:
            res = await self.client.retrieve(self.collection_name, ids=[memory_id])
            if res:
                return res[0].payload
        except Exception:
            logger.exception("Memory get error")
        return None

    async def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        await self._ensure_collection()
        try:
            query_filter = self._build_filter(user_id, agent_id, run_id, org_id, project_id, category, filters)

            records, _ = await self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            return [r.payload for r in records if r.payload and not self._is_expired(r.payload)]
        except Exception:
            logger.exception("Memory listing failed")
            return []

    def _is_expired(self, payload: Dict) -> bool:
        expires_at = payload.get("expires_at")
        if not expires_at:
            return False
        try:
            exp = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False

    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        if not user_id and not org_id and not project_id:
            return []

        try:
            query_filter = self._build_filter(user_id, agent_id, run_id, org_id, project_id, category, filters)

            await self._ensure_collection()
            vector = await self.embedder.embed_query(query)
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
                    recency_score = self._calculate_recency_score(mem.get("created_at", datetime.now(timezone.utc).isoformat()))
                    hybrid_score = semantic_score + doc_scores[i] + (recency_score * 2.0)
                    scored_memories.append((hybrid_score, mem))

                scored_memories.sort(key=lambda x: x[0], reverse=True)
                memories = [m for _, m in scored_memories]

            if len(memories) > limit:
                memories = memories[:limit]

            return memories
        except Exception:
            logger.exception("Memory search failed")
            return []

    async def get_memories(self, user_id: str, query: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> str:
        if query:
            results = await self.search(query, user_id=user_id, agent_id=agent_id, run_id=run_id)
        else:
            results = await self.get_all(user_id=user_id, agent_id=agent_id, run_id=run_id, limit=5)

        if not results:
            return ""

        memories = [m.get("text") for m in results if m.get("text")]
        if not memories:
            return ""

        formatted = "\n".join([f"- {m}" for m in memories])
        return f"Relevant Long-term Context:\n{formatted}\n"

    async def update(self, memory_id: str, new_content: str):
        try:
            await self._ensure_collection()
            vector = await self.embedder.embed_query(new_content)
            res = await self.client.retrieve(self.collection_name, ids=[memory_id])
            if res:
                payload = res[0].payload
                old_content = payload.get("text")
                payload["text"] = new_content
                payload["hash"] = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()

                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=[PointStruct(id=memory_id, vector=vector, payload=payload)]
                )
                create_background_task(
                    memory_manager.save_memory_history(
                        memory_id,
                        "UPDATE",
                        old_content,
                        new_content,
                    ),
                    f"memory-history-update-{memory_id}",
                )
                logger.info("Memory updated")
        except Exception:
            logger.exception("Memory update failed")

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
                create_background_task(
                    memory_manager.save_memory_history(
                        memory_id,
                        "DELETE",
                        old_content,
                        None,
                    ),
                    f"memory-history-delete-{memory_id}",
                )
                logger.info("Memory deleted")
        except Exception:
            logger.exception("Memory delete failed")

    delete_memory = delete

    async def delete_all(self, user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None, org_id: Optional[str] = None, project_id: Optional[str] = None, filters: Optional[Dict] = None):
        try:
            query_filter = self._build_filter(user_id, agent_id, run_id, org_id, project_id, None, filters)

            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=query_filter.must)
            )
            logger.info("Memory bulk delete completed")
        except Exception:
            logger.exception("Memory bulk delete failed")

    async def history(self, memory_id: str) -> List[Dict]:
        try:
            key = f"memory:history:{memory_id}"
            if memory_manager._redis:
                existing = await memory_manager._redis.get(key)
                if existing:
                    return json.loads(existing)
            return []
        except Exception:
            logger.exception("Memory history read error")
            return []

    async def get_context(self, query: str, user_id: str) -> str:
        return await self.get_memories(user_id, query)

    async def chat(self, query: str, user_id: str) -> str:
        context = await self.get_context(query, user_id)
        system_prompt = registry.get(PromptType.MEMORY_CHAT_ASSISTANT).format(context=context)
        try:
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=query)]
            response = await self.llm.ainvoke(msg)
            return response.content
        except Exception:
            logger.exception("Memory chat failed")
            raise RuntimeError("memory_chat_failed")

    @property
    def project(self):
        return self._project_store

    @property
    def entity_store(self):
        return self._entity_store

    async def reset(self):
        try:
            await self.client.delete_collection(self.collection_name)
            logger.info("Memory collection reset")
        except Exception:
            logger.exception("Memory collection reset failed")

    async def close(self):
        try:
            if hasattr(self.client, 'close'):
                await self.client.close()
            logger.info("Memory client closed")
        except Exception:
            logger.exception("Memory client close failed")

memo_manager = MemoryManager()
