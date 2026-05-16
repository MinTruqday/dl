import os
from loguru import logger
from typing import List, Dict, Optional
import json
import asyncio
from langchain_huggingface import HuggingFaceEndpoint

class ReasoningAgent:
    def __init__(self):
        self._model = os.environ.get("LLAMA_MODEL")
        self._hf_token = os.environ.get("HF_TOKEN")
        logger.info(f"Reasoning Agent initialized with model: {self._model}")

    async def evaluate_quality(self, query: str, answer: str, context_docs: List[Dict]) -> Dict:
        context_str = self._build_context(context_docs[:3])

        eval_prompt = f"""Hãy đánh giá chất lượng của cặp Câu hỏi và Câu trả lời sau. CHỈ trả về một khối JSON hợp lệ.

CÂU HỎI: {query}
CÂU TRẢ LỜI: {answer}
NGỮ CẢNH HIỆN CÓ: {context_str[:3000]}

Tiêu chí đánh giá tính theo thang 0.0 đến 1.0 (Giữ nguyên Key JSON):
1. "relevance": 0.0-1.0 (độ liên quan giữa câu trả lời và câu hỏi, có sử dụng ngữ cảnh hay không)
2. "grounding": 0.0-1.0 (độ chính xác, có bị ảo giác hay không, có bám sát ngữ cảnh hay không)
3. "completeness": 0.0-1.0 (độ đầy đủ, có trả lời hết ý câu hỏi hay không)
4. "overall": 0.0-1.0 (đánh giá tổng thể chất lượng câu trả lời, có thể là trung bình có trọng số của 3 tiêu chí trên)
5. "should_retry": bool (true nếu overall < 0.6)
6. "feedback": "Nhận xét ngắn gọn về điểm mạnh, điểm yếu của câu trả lời và gợi ý cải thiện nếu cần thiết."

Chỉ trả về định dạng JSON:"""

        try:
            llm = HuggingFaceEndpoint(
                repo_id=self._model,
                huggingfacehub_api_token=self._hf_token,
                temperature=0.1,
                max_new_tokens=300
            )
            result_text = await llm.ainvoke(eval_prompt)
            result_text = result_text.strip()
            
            if "```" in result_text:
                parts = result_text.split("```")
                for p in parts:
                    p = p.strip()
                    if p.startswith("json"):
                        result_text = p[4:].strip()
                        break
                    elif p.startswith("{"):
                        result_text = p
                        break
            
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"ReasoningAgent: Lỗi đánh giá: {e}")
            return {"overall": 0.5, "should_retry": False, "feedback": f"Lỗi đánh giá: {str(e)}"}

    def _build_context(self, docs: List[Dict]) -> str:
        if not docs:
            return "Không có tài liệu nào được tìm thấy."

        parts = []
        for i, doc in enumerate(docs[:5], 1):
            title = doc.get("metadata", {}).get("title", "Không rõ")
            author = doc.get("metadata", {}).get("author", "Không rõ")
            text = doc.get("text", "")[:800]
            parts.append(f"[Nguồn {i}] {title} - {author}\n{text}")

        return "\n\n".join(parts)

reasoning_agent = ReasoningAgent()
