import httpx
from core.config import settings
from loguru import logger

class TranslationService:
    def __init__(self):
        self._url = settings.NLLB_MODEL
        self._headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}

    async def translate(self, text: str, target_lang: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"inputs": text, "parameters": {"tgt_lang": target_lang}}
                response = await client.post(self._url, headers=self._headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    return result[0].get("translation_text", text)
                logger.error("The external neural language translation engine strictly rejected parsing submitted linguistic payload")
                return text
        except Exception:
            logger.error("The remote translation infrastructure definitively lost connection halting active language structural conversion")
            return text

translation_service = TranslationService()