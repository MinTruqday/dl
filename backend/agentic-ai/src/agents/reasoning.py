from loguru import logger
from typing import List, Dict
import json
from langchain_huggingface import HuggingFaceEndpoint
from src.core.config import settings

class ReasoningAgent:
    def __init__(self):
        self._model = settings.LLAMA_MODEL
        self._hf_token = settings.HF_TOKEN
        logger.info(f"ReasoningAgent: Initialized with model={self._model}")

    async def execute(self, task: str) -> str:
        logger.info(f"ReasoningAgent: Executing logic task: {task[:50]}")
        prompt = f"""SYSTEM IDENTITY: DocLib Core System - Analytical Engine.
OBJECTIVE: Perform deep logical analysis, evaluate cause-and-effect, and provide coherent conclusions.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

TASK: {task}

INSTRUCTIONS:
Provide a step-by-step logical breakdown of the problem before delivering the final conclusion."""
        try:
            llm = HuggingFaceEndpoint(
                repo_id=self._model,
                huggingfacehub_api_token=self._hf_token,
                temperature=0.2,
                max_new_tokens=1000
            )
            result = await llm.ainvoke(prompt)
            return result.strip()
        except Exception as e:
            logger.error(f"ReasoningAgent: Execution failed: {e}")
            return f"Lỗi suy luận: {str(e)}"

    async def evaluate_quality(self, query: str, answer: str, context_docs: List[Dict]) -> Dict:
        context_str = self._build_context(context_docs[:3])

        eval_prompt = f"""SYSTEM IDENTITY: DocLib Core System - Quality Evaluation Engine.
OBJECTIVE: Evaluate the quality of the generated response against the provided context.
OUTPUT_LANGUAGE: You must output ONLY a valid JSON object.

USER QUERY: {query}
GENERATED RESPONSE: {answer}
REFERENCE CONTEXT: {context_str[:3000]}

JSON SCHEMA:
{{
    "relevance": <float between 0.0 and 1.0>,
    "grounding": <float between 0.0 and 1.0>,
    "completeness": <float between 0.0 and 1.0>,
    "overall": <float between 0.0 and 1.0>,
    "should_retry": <boolean, true if overall < 0.6>,
    "feedback": "<string, concise feedback on strengths and weaknesses>"
}}

RULES:
- Output nothing but the requested JSON structure."""

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
            logger.error(f"ReasoningAgent: Quality evaluation failed: {e}")
            return {"overall": 0.5, "should_retry": False, "feedback": f"Evaluation error: {str(e)}"}

    def _build_context(self, docs: List[Dict]) -> str:
        if not docs:
            return "No documents found."

        parts = []
        for i, doc in enumerate(docs[:5], 1):
            title = doc.get("metadata", {}).get("title", "Unknown")
            author = doc.get("metadata", {}).get("author", "Unknown")
            text = doc.get("text", "")[:800]
            parts.append(f"[Source {i}] {title} - {author}\n{text}")

        return "\n\n".join(parts)

reasoning_agent = ReasoningAgent()
