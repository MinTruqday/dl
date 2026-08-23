import json
from types import SimpleNamespace
from typing import Any, AsyncIterator

import httpx
from loguru import logger

from src.core.infrastructure.configuration import settings


class LocalModelUnavailable(RuntimeError):
    pass


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


def _response(
    content: str, prompt_tokens: int = 0, completion_tokens: int = 0, model_used: str = ""
):
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    message = SimpleNamespace(content=content)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)], usage=usage, model=model_used
    )


class LocalModelClient:
    def __init__(self):
        self._primary_runtime_status = "unverified"

    async def _ollama_model_is_loaded(self) -> bool:
        """Return true only when Ollama already has the primary model in memory."""
        health_url = settings.PRIMARY_MODEL_HEALTH_URL.rstrip("/")
        ps_url = (
            health_url.rsplit("/", 1)[0] + "/ps" if health_url.endswith("/tags") else health_url
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(ps_url)
            response.raise_for_status()
            names = {
                item.get("name") or item.get("model") for item in response.json().get("models", [])
            }
            return any(
                settings.LLM_MODEL == name
                or settings.LLM_MODEL.split(":")[0] == str(name).split(":")[0]
                for name in names
                if name
            )
        except Exception:
            return False

    async def _ollama_completion(self, model, messages, max_tokens, temperature):
        payload = {
            "model": model,
            "messages": _ollama_messages(messages),
            "stream": False,
            "think": False,
            "keep_alive": settings.MODEL_KEEP_ALIVE,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(settings.PRIMARY_MODEL_URL, json=payload)
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
            settings.LLM_MODEL,
        )

    async def _openai_primary_completion(self, model, messages, max_tokens, temperature):
        headers = {"Content-Type": "application/json"}
        if settings.PRIMARY_MODEL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.PRIMARY_MODEL_API_TOKEN}"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT_SECONDS) as client:
            response = await client.post(settings.PRIMARY_MODEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        content = str(choices[0].get("message", {}).get("content", "")).strip() if choices else ""
        if not content:
            self._primary_runtime_status = "unavailable"
            raise LocalModelUnavailable("primary_model_empty_response")
        self._primary_runtime_status = "ready"
        usage = body.get("usage") or {}
        return _response(
            content,
            int(usage.get("prompt_tokens", 0) or 0),
            int(usage.get("completion_tokens", 0) or 0),
            str(body.get("model") or settings.LLM_MODEL),
        )

    async def _primary_completion(self, messages, max_tokens, temperature):
        if settings.PRIMARY_MODEL_STYLE == "ollama":
            return await self._ollama_completion(
                settings.LLM_MODEL, messages, max_tokens, temperature
            )
        if settings.PRIMARY_MODEL_STYLE == "openai":
            return await self._openai_primary_completion(
                settings.LLM_MODEL, messages, max_tokens, temperature
            )
        raise LocalModelUnavailable("primary_model_style_unsupported")

    def active_model(self) -> str:
        return settings.LLM_MODEL

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
            return self._stream(messages, max_tokens, temperature, model)
        try:
            return await self._primary_completion(messages, max_tokens, temperature)
        except Exception as primary_error:
            self._primary_runtime_status = "unavailable"
            logger.warning(
                "Configured model failed error_type={} model={}",
                type(primary_error).__name__,
                settings.LLM_MODEL,
            )
            raise LocalModelUnavailable("configured_model_unavailable") from primary_error

    async def warm_primary(self) -> None:
        try:
            await self._primary_completion([{"role": "user", "content": "Reply OK"}], 4, 0)
        except Exception:
            self._primary_runtime_status = "unavailable"

    async def _stream(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        model: str | None = None,
    ) -> AsyncIterator[Any]:
        if settings.PRIMARY_MODEL_STYLE == "ollama":
            payload = {
                "model": settings.LLM_MODEL,
                "messages": _ollama_messages(messages),
                "stream": True,
                "think": False,
                "keep_alive": settings.MODEL_KEEP_ALIVE,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            }
            emitted = False
            prompt_tokens = 0
            completion_tokens = 0
            try:
                async with httpx.AsyncClient(timeout=settings.MODEL_TIMEOUT_SECONDS) as client:
                    async with client.stream(
                        "POST", settings.PRIMARY_MODEL_URL, json=payload
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line.strip():
                                continue
                            body = json.loads(line)
                            prompt_tokens = int(
                                body.get("prompt_eval_count", prompt_tokens) or prompt_tokens
                            )
                            completion_tokens = int(
                                body.get("eval_count", completion_tokens) or completion_tokens
                            )
                            token = str(body.get("message", {}).get("content", ""))
                            if token:
                                emitted = True
                                delta = SimpleNamespace(content=token)
                                yield SimpleNamespace(choices=[SimpleNamespace(delta=delta)])
                if not emitted:
                    raise LocalModelUnavailable("configured_model_empty_response")
                from src.services.token_accounting import record_usage

                record_usage(
                    _response("", prompt_tokens, completion_tokens, settings.LLM_MODEL),
                    sum(len(str(message.get("content", ""))) for message in messages),
                    0,
                )
                self._primary_runtime_status = "ready"
                return
            except Exception as error:
                self._primary_runtime_status = "unavailable"
                raise LocalModelUnavailable("configured_model_unavailable") from error

        response = await self.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        content = response.choices[0].message.content
        for token in content.splitlines(keepends=True) or [content]:
            delta = SimpleNamespace(content=token)
            yield SimpleNamespace(choices=[SimpleNamespace(delta=delta)])

    async def readiness(self) -> dict[str, str]:
        checks = {"model": "unavailable"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                headers = {}
                if settings.PRIMARY_MODEL_API_TOKEN:
                    headers["Authorization"] = f"Bearer {settings.PRIMARY_MODEL_API_TOKEN}"
                response = await client.get(settings.PRIMARY_MODEL_HEALTH_URL, headers=headers)
                if response.status_code == 200:
                    if settings.PRIMARY_MODEL_STYLE == "ollama":
                        available = await self._ollama_model_is_loaded()
                        self._primary_runtime_status = "ready" if available else "unavailable"
                    else:
                        available = True
                    if available:
                        checks["model"] = (
                            "ready"
                            if self._primary_runtime_status != "unavailable"
                            else "unavailable"
                        )
            except Exception:
                pass
        return checks


local_model_client = LocalModelClient()
