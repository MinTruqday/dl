import os
import httpx
from fastapi import HTTPException
from loguru import logger
import json

class AgentService:
    @staticmethod
    async def process_text(req):
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if not rag_url:
            logger.error("AGENTIC_RAG_URL not set")
            raise HTTPException(status_code=500, detail="Cấu hình dịch vụ AI chưa hoàn tất.")

        try:
            async with httpx.AsyncClient() as client:
                if req.action == "translate":
                    res = await client.post(
                        f"{rag_url}/api/inference/translate",
                        json={"text": req.text, "target_lang": req.target_lang},
                        timeout=30.0
                    )
                    res.raise_for_status()
                    return {"status": "success", "result": res.json().get("translation", "")}
                else:
                    prompt = ""
                    if req.action == "autocomplete":
                        prompt = f"Write the next reasonable sentence for this text without echoing my text. Context: {req.context}. Text: {req.text}"
                    elif req.action == "grammar":
                        prompt = f"Fix all grammar and spelling mistakes in the following text. Only return the corrected text without any extra explanations: {req.text}"
                    elif req.action == "summarize":
                        prompt = f"Provide a clean, concise summary of the following text: {req.text}"
                    else:
                        raise HTTPException(status_code=400, detail="Hành động xử lý văn bản không hợp lệ.")

                    res = await client.post(
                        f"{rag_url}/api/inference/generate",
                        json={"prompt": prompt, "max_tokens": 150},
                        timeout=30.0
                    )
                    res.raise_for_status()
                    return {"status": "success", "result": res.json().get("result", "")}

        except Exception as e:
            logger.error(f"AI text processing error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi xử lý văn bản với AI.")

    @staticmethod
    async def process_document(req):
        rag_url = os.environ.get("AGENTIC_RAG_URL")
        if not rag_url:
            logger.error("AGENTIC_RAG_URL not set")
            raise HTTPException(status_code=500, detail="Cấu hình dịch vụ AI chưa hoàn tất.")

        try:
            async with httpx.AsyncClient() as client:
                if req.action == "flashcard":
                    prompt = f"""You are an English/Vocab/Concept teacher. Given the highlighted text and its surrounding context, output a JSON object with 'front' (the concept/question) and 'back' (the explanation/summarized meaning). Return exactly this JSON structure: {{"front": "...", "back": "..."}} Do not output any additional text or markdown formatting. Highlighted Text: {req.text} Context: {req.context}"""
                    res = await client.post(
                        f"{rag_url}/api/inference/generate_raw",
                        json={"prompt": prompt, "max_tokens": 200, "temperature": 0.3},
                        timeout=30.0
                    )
                    res.raise_for_status()
                    text_resp = res.json().get("result", "")
                    if text_resp.startswith("```json"):
                        text_resp = text_resp[7:-3]
                    
                    try:
                        return {"status": "success", "result": json.loads(text_resp)}
                    except Exception as json_err:
                        logger.error(f"Invalid JSON from AI: {json_err}. Raw: {text_resp}")
                        return {"status": "error", "message": "Kết quả AI không đúng định dạng.", "raw": text_resp}
                else:
                    raise HTTPException(status_code=400, detail="Hành động xử lý tài liệu không hợp lệ.")
        except Exception as e:
            logger.error(f"AI document processing error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi xử lý tài liệu với AI.")
