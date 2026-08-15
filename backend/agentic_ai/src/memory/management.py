from typing import Dict, List, Optional

from src.memory.long_term import LongTermMemory, long_term_memory
from src.memory.short_term import ShortTermMemory, short_term_memory


class MemoryManager:
    """Small facade over session memory and persistent user memory."""

    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None,
    ):
        self.short_term = short_term or short_term_memory
        self.long_term = long_term or long_term_memory

    @property
    def _redis(self):
        return self.short_term._redis

    async def get_short_term(self, session_id: str) -> List[Dict]:
        return await self.short_term.get_short_term(session_id)

    async def save_short_term(self, session_id: str, entry: Dict) -> None:
        await self.short_term.save_short_term(session_id, entry)

    async def clear_short_term(self, session_id: str) -> None:
        await self.short_term.clear(session_id)

    async def add(self, messages: List[Dict], user_id: Optional[str] = None) -> None:
        await self.long_term.add(messages, user_id)

    add_memory = add

    async def search(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        return await self.long_term.search(query, user_id, limit)

    async def get_memories(
        self, user_id: str, query: Optional[str] = None
    ) -> str:
        return await self.long_term.get_memories(user_id, query)

    async def update(self, memory_id: str, new_content: str) -> None:
        await self.long_term.update(memory_id, new_content)

    update_memory = update

    async def delete(self, memory_id: str) -> None:
        await self.long_term.delete(memory_id)

    delete_memory = delete

    async def close(self) -> None:
        await self.long_term.close()
        await self.short_term.close()


memory_manager = MemoryManager()
