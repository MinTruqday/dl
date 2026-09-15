import contextvars
import uuid

from fastapi import Request

trace_id_ctx_var = contextvars.ContextVar("trace_id", default="")


def trace_id_filter(record):
    record["extra"]["trace_id"] = trace_id_ctx_var.get()
    return True


async def add_trace_id_header(request: Request, call_next):
    trace_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id_ctx_var.set(trace_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = trace_id
    return response


from fastapi import Request
