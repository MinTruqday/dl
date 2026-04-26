from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import asyncio
from src.memory.cache_manager import semantic_cache

router = APIRouter()

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.3

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

class SentimentRequest(BaseModel):
    texts: List[str]

class GrammarRequest(BaseModel):
    text: str

class SynonymsRequest(BaseModel):
    word: str
    context: Optional[str] = ""


class CoverRequest(BaseModel):
    title: str
    description: str = ""
    style: str = "minimalist"

class FlashcardRequest(BaseModel):
    text: str
    context: str = ""

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/generate")
async def generate_text(req: GenerationRequest):
    try:
        cached_result = semantic_cache.get_cache(req.prompt)
        if cached_result:
            return {"result": cached_result, "cached": True}

        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        def run_model():
            from transformers import pipeline
            pipe = pipeline("text-generation", model=model_name, max_new_tokens=req.max_tokens, token=hf_token)
            messages = [{"role": "user", "content": req.prompt}]
            out = pipe(messages)
            try:
                return out[0]["generated_text"][-1]["content"].strip()
            except Exception as e:
                import logging; logging.error(f"RAG Error: {e}")
                return str(out)
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_model)
        semantic_cache.set_cache(req.prompt, result)
        return {"result": result, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_raw")
async def generate_raw_text(req: GenerationRequest):
    try:
        cached_result = semantic_cache.get_cache(req.prompt)
        if cached_result:
            return {"result": cached_result, "cached": True}

        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        def run_model():
            from transformers import pipeline
            pipe = pipeline("text-generation", model=model_name, max_new_tokens=req.max_tokens, token=hf_token)
            res = pipe(req.prompt, temperature=req.temperature)
            return res[0]["generated_text"].replace(req.prompt, "").strip()
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_model)
        semantic_cache.set_cache(req.prompt, result)
        return {"result": result, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate")
async def translate_text(req: TranslationRequest):
    try:
        def run_translation():
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            lang_map = {
                "Vietnamese": "vie_Latn", "vi": "vie_Latn",
                "English": "eng_Latn", "en": "eng_Latn",
                "French": "fra_Latn", "fr": "fra_Latn",
                "Spanish": "spa_Latn", "es": "spa_Latn"
            }
            tgt_code = lang_map.get(req.target_lang, "vie_Latn")
            model_id = os.environ.get("NLLB_MODEL")
            hf_token = os.environ.get("HF_TOKEN")
            
            tokenizer = AutoTokenizer.from_pretrained(model_id, src_lang="eng_Latn", token=hf_token)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id, token=hf_token)

            inputs = tokenizer(req.text, return_tensors="pt")
            forced_bos_token_id = tokenizer.lang_code_to_id.get(tgt_code, tokenizer.lang_code_to_id["vie_Latn"])
            translated_tokens = model.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=150)
            return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_translation)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
            
@router.post("/analyze-sentiment")
async def analyze_sentiment(req: SentimentRequest):
    try:
        combined_text = "\n---\n".join(req.texts[:20])
        prompt = f"Phân tích cảm xúc của các đánh giá sau đây. Trả về kết quả JSON với các trường: sentiment (positive/neutral/negative), positive_pct, negative_pct, summary (tóm tắt ngắn gọn).\n\nĐánh giá:\n{combined_text}\n\nJSON:"
        
        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        
        async def call_llm():
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model_name, huggingfacehub_api_token=hf_token, temperature=0.1)
            res = await llm.ainvoke(prompt)

            import json
            import re
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"sentiment": "neutral", "summary": "Không thể phân tích chính xác."}

        result = await call_llm()
        return result
    except Exception as e:
        import logging; logging.error(f"Sentiment Error: {e}")
        return {"sentiment": "neutral", "summary": f"Lỗi: {str(e)}"}

@router.post("/grammar-check")
async def check_grammar(req: GrammarRequest):
    try:
        prompt = f"Kiểm tra ngữ pháp và lỗi chính tả cho đoạn văn sau. Trả về JSON gồm: issues (danh sách lỗi), score (0-100), message (nhận xét chung).\n\nĐoạn văn: {req.text[:2000]}\n\nJSON:"
        
        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        
        async def call_llm():
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model_name, huggingfacehub_api_token=hf_token, temperature=0.1)
            res = await llm.ainvoke(prompt)
            import json
            import re
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"score": 100, "message": "Không tìm thấy lỗi."}

        result = await call_llm()
        return result
    except Exception as e:
        return {"score": 0, "message": f"Lỗi AI: {str(e)}"}

@router.post("/generate-cover")
async def generate_cover(req: CoverRequest):
    import urllib.parse
    encoded_title = urllib.parse.quote(req.title)
    placeholder_url = f"https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=1000&auto=format&fit=crop" 
    return {"cover_url": placeholder_url, "message": "Ảnh bìa đã được khởi tạo theo phong cách tối giản."
    }

@router.post("/generate-flashcard")
async def generate_flashcard(req: FlashcardRequest):
    try:
        prompt = f"Bạn là một giáo viên. Dựa trên văn bản được cung cấp, hãy tạo một Flashcard dưới định dạng JSON với các trường: front (câu hỏi/khái niệm) và back (giải thích/câu trả lời ngắn gọn).\n\nVăn bản: {req.text}\nBối cảnh: {req.context}\n\nJSON:"
        
        cached_result = semantic_cache.get_cache(prompt)
        if cached_result:
            import json
            try:
                return json.loads(cached_result)
            except:
                pass

        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        
        async def call_llm():
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model_name, huggingfacehub_api_token=hf_token, temperature=0.3)
            res = await llm.ainvoke(prompt)
            import json
            import re
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"front": req.text, "back": "Không thể tạo giải thích tự động."}

        result = await call_llm()
        import json
        semantic_cache.set_cache(prompt, json.dumps(result))
        return result
    except Exception as e:
        import logging; logging.error(f"Flashcard Error: {e}")
        return {"front": req.text, "back": f"Lỗi AI: {str(e)}"}

from src.memory.conversation_memory import conversation_memory

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:

        cached_result = semantic_cache.get_cache(req.message)
        if cached_result:

            await conversation_memory.add_message(req.session_id, "user", req.message)
            await conversation_memory.add_message(req.session_id, "ai", cached_result)
            return {"result": cached_result, "cached": True}


        history_context = conversation_memory.get_context(req.session_id)
        
        prompt = f"Bạn là một trợ lý AI hữu ích. Dưới đây là ngữ cảnh cuộc trò chuyện:\n{history_context}\n\nUser: {req.message}\nAI:"
        
        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        
        async def call_llm():
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model_name, huggingfacehub_api_token=hf_token, temperature=0.5)
            return await llm.ainvoke(prompt)
            
        result = await call_llm()
        result = result.strip()
        

        semantic_cache.set_cache(req.message, result)
        

        await conversation_memory.add_message(req.session_id, "user", req.message)
        await conversation_memory.add_message(req.session_id, "ai", result)
        
        return {"result": result, "cached": False}
    except Exception as e:
        return {"result": f"Lỗi AI: {str(e)}"}

@router.post("/synonyms")
async def get_synonyms(req: SynonymsRequest):
    try:
        prompt = f"Liệt kê 5 từ đồng nghĩa với từ '{req.word}' trong ngữ cảnh: '{req.context}'. Chỉ trả về danh sách các từ cách nhau bởi dấu phẩy, không giải thích thêm."
        
        model_name = os.environ.get('LLAMA_MODEL')
        hf_token = os.environ.get("HF_TOKEN")
        
        async def call_llm():
            from langchain_huggingface import HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model_name, huggingfacehub_api_token=hf_token, temperature=0.1)
            return await llm.ainvoke(prompt)
            
        result = await call_llm()
        synonyms = [s.strip() for s in result.split(",")]
        return {"synonyms": synonyms}
    except Exception as e:
        return {"synonyms": [], "error": str(e)}

