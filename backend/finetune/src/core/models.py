import json

import httpx
from huggingface_hub import HfApi

from src.core.infrastructure.configuration import settings
from src.schemas.contracts import GeneratedSamples


def resolve_model_revision(model_id: str, token: str | None = None) -> str:
    info = HfApi(token=token).model_info(model_id)
    if not info.sha:
        raise RuntimeError(f"Unable to resolve immutable model revision: {model_id}")
    return info.sha


async def generate_text(prompt: str, model: str | None = None) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_URL}/api/chat",
            json={
                "model": model or settings.LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
    response.raise_for_status()
    return str(response.json().get("message", {}).get("content", ""))


async def generate_training_samples(chunk: str) -> list[dict]:
    prompt = (
        "Create 1 to 3 grounded instruction/input/output training samples from "
        "the source. Do not add facts absent from the source.\n\nSOURCE:\n"
        + chunk
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_URL}/api/chat",
            json={
                "model": settings.LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "format": GeneratedSamples.model_json_schema(),
                "stream": False,
            },
        )
    response.raise_for_status()
    content = response.json().get("message", {}).get("content", "{}")
    parsed = GeneratedSamples.model_validate(json.loads(content))
    return [sample.model_dump() for sample in parsed.samples]
