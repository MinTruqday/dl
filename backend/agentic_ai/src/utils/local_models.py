import asyncio
from types import SimpleNamespace
from typing import Any, AsyncIterator

import httpx
from loguru import logger

from src.core.infrastructure.configuration import settings


class LocalModelUnavailable(RuntimeError):
    pass


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _data_value(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("url", "")
    text = str(value or "")
    return text.split(",", 1)[1] if text.startswith("data:") and "," in text else text


def _ollama_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted = []
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            converted.append({"role": message.get("role", "user"), "content": content})
            continue
        texts = []
        media = []
        for item in content if isinstance(content, list) else []:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text":
                texts.append(str(item.get("text", "")))
            elif item_type == "image_url":
                media.append(_data_value(item.get("image_url")))
            elif item_type in {"audio_url", "input_audio"}:
                media.append(_data_value(item.get("audio_url") or item.get("input_audio")))
        entry = {"role": message.get("role", "user"), "content": "\n".join(texts)}
        if media:
            entry["images"] = media
        converted.append(entry)
    return converted


def _response(content: str, prompt_tokens: int = 0, completion_tokens: int = 0):
    usage = SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    message = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


class LocalModelClient:
    def __init__(self):
        self._primary_runtime_status = "unverified"

    async def _ollama_completion(self, model, messages, max_tokens, temperature):
        payload = {
            "model": model,
            "messages": _ollama_messages(messages),
            "stream": False,
            "think": False,
            "keep_alive": settings.MODEL_KEEP_ALIVE,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                _url(settings.OLLAMA_BASE_URL, "/api/chat"),
                json=payload,
            )
        response.raise_for_status()
        body = response.json()
        content = str(body.get("message", {}).get("content", "")).strip()
        if not content:
            self._primary_runtime_status = "unavailable"
            raise LocalModelUnavailable("primary_model_empty_response")
        self._primary_runtime_status = "ready"
        return _response(
            content,
            int(body.get("prompt_eval_count", 0) or 0),
            int(body.get("eval_count", 0) or 0),
        )

    async def _qwen_completion(self, messages, max_tokens, temperature):
        if not settings.QWEN_API_URL.strip():
            raise LocalModelUnavailable("fallback_endpoint_not_configured")
        payload = {
            "inputs": messages,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.HF_TOKEN}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(
                settings.QWEN_API_URL,
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        content = (
            str(choices[0].get("message", {}).get("content", "")).strip()
            if choices
            else ""
        )
        if not content:
            raise LocalModelUnavailable("fallback_model_empty_response")
        usage = body.get("usage") or {}
        return _response(
            content,
            int(usage.get("prompt_tokens", 0) or 0),
            int(usage.get("completion_tokens", 0) or 0),
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stream: bool = False,
        **_: Any,
    ):
        if stream:
            return self._stream(messages, max_tokens, temperature)
        try:
            return await self._ollama_completion(
                settings.LLM_MODEL,
                messages,
                max_tokens,
                temperature,
            )
        except Exception as primary_error:
            self._primary_runtime_status = "unavailable"
            logger.warning(
                "Primary local model failed error_type={} fallback_model={}",
                type(primary_error).__name__,
                settings.QWEN_MODEL,
            )
            try:
                return await self._qwen_completion(messages, max_tokens, temperature)
            except Exception as fallback_error:
                raise LocalModelUnavailable("all_local_models_unavailable") from fallback_error

    async def warm_primary(self) -> None:
        for attempt in range(3):
            try:
                await self._ollama_completion(
                    settings.LLM_MODEL,
                    [{"role": "user", "content": "Reply OK"}],
                    4,
                    0,
                )
                return
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(30)

    async def _stream(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
    ) -> AsyncIterator[Any]:
        response = await self.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        content = response.choices[0].message.content
        for token in content.splitlines(keepends=True) or [content]:
            delta = SimpleNamespace(content=token)
            yield SimpleNamespace(choices=[SimpleNamespace(delta=delta)])

    async def readiness(self) -> dict[str, str]:
        checks = {"primary_model": "unavailable", "fallback_model": "unavailable"}
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.get(_url(settings.OLLAMA_BASE_URL, "/api/tags"))
                names = {item.get("name") for item in response.json().get("models", [])}
                if response.status_code == 200:
                    if any(settings.LLM_MODEL == n or settings.LLM_MODEL.split(":")[0] == n.split(":")[0] for n in names):
                        checks["primary_model"] = self._primary_runtime_status
            except Exception:
                pass
            if not settings.QWEN_API_URL.strip():
                checks["fallback_model"] = "not_configured"
            elif not settings.QWEN_HEALTH_URL.strip():
                checks["fallback_model"] = "unknown"
            else:
                try:
                    response = await client.get(
                        settings.QWEN_HEALTH_URL,
                        headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
                    )
                    if response.status_code == 200:
                        checks["fallback_model"] = "ready"
                except Exception:
                    pass
        return checks


local_model_client = LocalModelClient()
