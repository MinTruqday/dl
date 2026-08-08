from typing import Any, Dict, List, Optional

from src.memory.long_term import LongTermMemory, long_term_memory
from src.memory.short_term import ShortTermMemory, short_term_memory

class MemoryManager:
    def __init__(self, short_term: Optional[ShortTermMemory] = None, long_term: Optional[LongTermMemory] = None):
        self.short_term = short_term or short_term_memory
        self.long_term = long_term or long_term_memory

    @property
    def _redis(self):
        return self.short_term._redis

    @property
    def llm(self):
        return self.long_term.llm

    @property
    def embedder(self):
        return self.long_term.embedder

    @property
    def collection_name(self):
        return self.long_term.collection_name

    @property
    def client(self):
        return self.long_term.client

    @property
    def entity_store(self):
        return self.long_term.entity_store

    @property
    def project(self):
        return self.long_term.project

    async def get_short_term(self, conversation_id: str) -> List[Dict]:
        return await self.short_term.get_short_term(conversation_id)

    async def save_short_term(self, conversation_id: str, entry: Dict):
        await self.short_term.save_short_term(conversation_id, entry)

    async def save_long_term(self, user_id: str, entry: Dict):
        await self.short_term.save_long_term(user_id, entry)

    async def get_long_term(self, user_id: str) -> List[Dict]:
        return await self.short_term.get_long_term(user_id)

    async def get_user_preferences(self, user_id: str) -> Dict:
        return await self.short_term.get_user_preferences(user_id)

    async def save_memory_history(self, memory_id: str, action: str, old_text: Optional[str], new_text: Optional[str]):
        await self.short_term.save_memory_history(memory_id, action, old_text, new_text)

    async def add(self, messages: List[Dict], user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None, org_id: Optional[str] = None, project_id: Optional[str] = None, category: Optional[str] = None, memory_scope: str = "user"):
        return await self.long_term.add(messages, user_id=user_id, agent_id=agent_id, run_id=run_id, org_id=org_id, project_id=project_id, category=category, memory_scope=memory_scope)

    add_memory = add

    async def batch_add(self, batch_items: List[Dict[str, Any]]):
        return await self.long_term.batch_add(batch_items)

    async def batch_update(self, updates: List[Dict[str, str]]):
        return await self.long_term.batch_update(updates)

    async def batch_delete(self, memory_ids: List[str]):
        return await self.long_term.batch_delete(memory_ids)

    async def get(self, memory_id: str) -> Optional[Dict]:
        return await self.long_term.get(memory_id)

    async def get_all(self, user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None, org_id: Optional[str] = None, project_id: Optional[str] = None, category: Optional[str] = None, limit: int = 100, filters: Optional[Dict] = None) -> List[Dict]:
        return await self.long_term.get_all(user_id=user_id, agent_id=agent_id, run_id=run_id, org_id=org_id, project_id=project_id, category=category, limit=limit, filters=filters)

    async def search(self, query: str, user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None, org_id: Optional[str] = None, project_id: Optional[str] = None, category: Optional[str] = None, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        return await self.long_term.search(query=query, user_id=user_id, agent_id=agent_id, run_id=run_id, org_id=org_id, project_id=project_id, category=category, limit=limit, filters=filters)

    async def get_memories(self, user_id: str, query: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None) -> str:
        return await self.long_term.get_memories(user_id=user_id, query=query, agent_id=agent_id, run_id=run_id)

    async def update(self, memory_id: str, new_content: str):
        return await self.long_term.update(memory_id, new_content)

    update_memory = update

    async def delete(self, memory_id: str):
        return await self.long_term.delete(memory_id)

    delete_memory = delete

    async def delete_all(self, user_id: Optional[str] = None, agent_id: Optional[str] = None, run_id: Optional[str] = None, org_id: Optional[str] = None, project_id: Optional[str] = None, filters: Optional[Dict] = None):
        return await self.long_term.delete_all(user_id=user_id, agent_id=agent_id, run_id=run_id, org_id=org_id, project_id=project_id, filters=filters)

    async def history(self, memory_id: str) -> List[Dict]:
        return await self.long_term.history(memory_id)

    async def get_context(self, query: str, user_id: str) -> str:
        return await self.long_term.get_context(query, user_id)

    async def chat(self, query: str, user_id: str) -> str:
        return await self.long_term.chat(query, user_id)

    async def users(self) -> List[str]:
        return await self.long_term.users()

    async def agents(self) -> List[str]:
        return await self.long_term.agents()

    async def runs(self) -> List[str]:
        return await self.long_term.runs()

    async def reset(self):
        await self.long_term.reset()

    async def close(self):
        await self.long_term.close()

ManagementMemory = MemoryManager
memory_manager = MemoryManager()
