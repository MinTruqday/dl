import os
from datetime import datetime
from loguru import logger
class ConversationMemory:
    def __init__(self, max_recent_turns=5):
        self.max_recent_turns = max_recent_turns
        self.conversations = {}
    def get_context(self, session_id: str) -> str:
        if session_id not in self.conversations:
            return ""
        mem = self.conversations[session_id]
        context = ""
        if mem.get("summary"):
            context += f"Tóm tắt trước đó: {mem['summary']}\n\n"
        if mem.get("recent_messages"):
            context += "Hội thoại gần đây:\n"
            for msg in mem["recent_messages"]:
                role = "User" if msg["role"] == "user" else "AI"
                context += f"{role}: {msg['content']}\n"
        return context.strip()
    async def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "summary": "",
                "recent_messages": [],
                "updated_at": datetime.utcnow()
            }
        mem = self.conversations[session_id]
        mem["recent_messages"].append({"role": role, "content": content})
        mem["updated_at"] = datetime.utcnow()
        if len(mem["recent_messages"]) > self.max_recent_turns * 2:
            await self._summarize_oldest(session_id)
    async def _summarize_oldest(self, session_id: str):
        mem = self.conversations[session_id]
        keep_count = self.max_recent_turns
        messages_to_summarize = mem["recent_messages"][:-keep_count]
        if not messages_to_summarize:
            return
        text_to_summarize = "\n".join([f"{'User' if m['role']=='user' else 'AI'}: {m['content']}" for m in messages_to_summarize])
        current_summary = mem.get("summary", "")
        prompt = f"Tóm tắt ngắn gọn nội dung cốt lõi của phần hội thoại sau. Nếu đã có tóm tắt cũ, hãy gộp chúng lại một cách tự nhiên.\n\nTóm tắt cũ: {current_summary}\n\nHội thoại cần tóm tắt:\n{text_to_summarize}\n\nTóm tắt mới:"
        try:
            model_name = os.environ.get('LLAMA_MODEL')
            hf_token = os.environ.get("HF_TOKEN")
            from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
            _hf = HuggingFaceEndpoint(
                repo_id=model_name,
                huggingfacehub_api_token=hf_token,
                temperature=0.1,
                task="conversational"
            )
            llm = ChatHuggingFace(llm=_hf)
            response = await llm.ainvoke(prompt)
            new_summary = response.content.strip()
            mem["summary"] = new_summary
            mem["recent_messages"] = mem["recent_messages"][-keep_count:]
            logger.info(f"Summarized session {session_id} memory to save context window.")
        except Exception as e:
            logger.error(f"Error summarizing memory for session {session_id}: {e}")
conversation_memory = ConversationMemory()
