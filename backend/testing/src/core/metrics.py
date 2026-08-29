import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


REQUESTS = Counter("qa_http_requests_total", "QA HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("qa_http_request_duration_seconds", "QA HTTP latency", ["path"])
RAG_LATENCY = Histogram("rag_latency", "Project RAG operation latency", ["operation"])
AI_GENERATION_LATENCY = Histogram("ai_generation_latency", "AI generation operation latency", ["operation"])
IMPACT_LATENCY = Histogram("impact_latency", "Impact analysis latency")
IMPACT_FAILED = Counter("impact_failed", "Failed impact analyses")
PROPOSAL_ACCEPTANCE_RATE = Gauge("proposal_acceptance_rate", "Accepted or edited proposals divided by reviewed proposals")
TRACE_ACCEPTANCE_RATE = Gauge("trace_acceptance_rate", "Confirmed trace links divided by reviewed trace links")
UNCOVERED = Gauge("requirements_uncovered", "Requirements without confirmed tests")
STALE = Gauge("tests_stale", "Test cases needing maintenance")


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        started_at = time.perf_counter()
        with LATENCY.labels(path).time():
            try:
                response = await call_next(request)
            except Exception:
                if path.endswith("/impact-analysis"):
                    IMPACT_FAILED.inc()
                raise
        if path.endswith("/impact-analysis"):
            IMPACT_LATENCY.observe(time.perf_counter() - started_at)
            if response.status_code >= 400:
                IMPACT_FAILED.inc()
        REQUESTS.labels(request.method, request.url.path, response.status_code).inc()
        return response


async def metrics_endpoint(request=None):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
