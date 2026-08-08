import json
from typing import AsyncGenerator, Any

class WorkflowStreamer:
    @staticmethod
    async def format_sse_event(event_type: str, data: Any) -> str:
        payload = json.dumps(data) if not isinstance(data, str) else data
        return f"event: {event_type}\ndata: {payload}\n\n"

    @staticmethod
    async def stream_tokens(token_generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        async for token in token_generator:
            yield await WorkflowStreamer.format_sse_event("token", {"content": token})
