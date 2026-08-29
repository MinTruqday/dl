import asyncio
from typing import List

from src.agents.harness.security import security
from src.core.infrastructure.configuration import settings
from src.core.model_runtime import run_chat_completion
from src.core.registry import PromptType, registry
from src.core.security.guardrails import guardrails_engine
from src.schemas.routing import CrossDocumentQueries, MultiQueryOutput
from src.utils.local_models import local_model_client
from src.utils.structured_output import validate_structured_output


async def chat(
    messages: List[dict],
    max_tokens: int = 500,
    temperature: float = 0.2,
    attempts: int = 1,
    timeout_seconds: int = 60,
):
    return await run_chat_completion(
        client=local_model_client,
        messages=messages,
        model=settings.LLM_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        attempts=attempts,
        timeout_seconds=timeout_seconds,
    )


async def structured(prompt, schema, max_tokens=1200, timeout_seconds=90):
    raw = await chat(
        [{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,
        attempts=3,
        timeout_seconds=timeout_seconds,
    )
    try:
        return validate_structured_output(raw, schema)
    except Exception:
        corrected = await chat(
            [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": raw[:4000]},
                {"role": "user", "content": "Return one corrected strictly valid JSON object only"},
            ],
            max_tokens=max_tokens,
            temperature=0,
            attempts=2,
            timeout_seconds=timeout_seconds,
        )
        return validate_structured_output(corrected, schema)


async def expand_retrieval(question: str) -> dict:
    hypothetical_document = await chat(
        [
            {
                "role": "user",
                "content": registry.get(PromptType.HYDE_GENERATION).format(question=question),
            }
        ],
        max_tokens=384,
        timeout_seconds=20,
    )
    result = await structured(
        registry.get(PromptType.MULTI_QUERY).format(question=question),
        MultiQueryOutput,
        max_tokens=192,
        timeout_seconds=20,
    )
    return {
        "hypothetical_document": hypothetical_document.strip() or question,
        "queries": [value.strip() for value in result.queries if value.strip()][:5],
    }


async def decompose_retrieval(question: str, document_ids: list[str]) -> list[str]:
    result = await structured(
        registry.get(PromptType.CROSS_DOCUMENT_QUERY).format(
            question=question, document_ids=document_ids
        ),
        CrossDocumentQueries,
        max_tokens=min(1024, 96 * len(document_ids)),
        timeout_seconds=20,
    )
    queries = [value.strip() for value in result.queries if value.strip()]
    if len(queries) != len(document_ids):
        raise ValueError("cross_document_decomposition_invalid")
    return queries


async def inspect_chunks(texts: list[str]) -> set[int]:
    semaphore = asyncio.Semaphore(4)

    async def inspect(index, text):
        async with semaphore:
            result = await security.ascan_input(text)
            return index if result.passed else None

    values = await asyncio.gather(
        *[inspect(index, text) for index, text in enumerate(texts)]
    )
    return {value for value in values if value is not None}


async def summarize_document(text: str) -> str:
    inspected = await guardrails_engine.async_inspect_input(text)
    if not inspected.get("is_safe", False):
        raise ValueError("knowledge_summary_input_unsafe")
    summary = await chat(
        [
            {
                "role": "user",
                "content": registry.get(PromptType.DOCUMENT_GLOBAL_SUMMARY).format(
                    text=inspected.get("sanitized_text") or text
                ),
            }
        ],
        max_tokens=512,
    )
    return summary.strip()
