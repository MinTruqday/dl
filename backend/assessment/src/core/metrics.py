import time
from collections import defaultdict
from uuid import uuid4

from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware


REQUIRED_GAUGES = {
    "assessment_import_duration": 0,
    "question_mapping_confidence": 0,
    "difficulty_prediction_mae": 0,
    "difficulty_prediction_confidence": 0,
    "calibration_valid_n": 0,
    "calibration_failure_rate": 0,
    "irt_fit_failure_rate": 0,
    "teacher_revision_acceptance_rate": 0,
    "construct_preservation_failure_rate": 0,
    "adaptive_session_question_count": 0,
    "student_ability_confidence": 0,
}

REQUIRED_COUNTERS = {
    "question_validation_failures": 0,
    "cross_tenant_filter_denials": 0,
}


class MetricsCollector:
    def __init__(self):
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(float)
        self.error_count = defaultdict(int)
        self.counters = defaultdict(float, REQUIRED_COUNTERS)
        self.gauges = dict(REQUIRED_GAUGES)

    def record_request(self, method: str, path: str, status_code: int, duration: float):
        key = (method, path)
        self.request_count[key] += 1
        self.request_duration[key] += duration
        if status_code >= 500:
            self.error_count[key] += 1

    def increment(self, name: str, value: float = 1):
        self.counters[name] += value

    def set(self, name: str, value: float):
        self.gauges[name] = float(value)

    def record_outcome(self, prefix: str, gauge_name: str, success: bool):
        self.increment(f"{prefix}_total")
        if success:
            self.increment(f"{prefix}_success")
        total = self.counters[f"{prefix}_total"]
        successes = self.counters[f"{prefix}_success"]
        self.set(gauge_name, successes / total if total else 0)

    def render(self, service_name: str):
        lines = []
        for (method, path), count in sorted(self.request_count.items()):
            labels = f'service="{service_name}",method="{method}",path="{path}"'
            lines.append(f"http_requests_total{{{labels}}} {count}")
            lines.append(f"http_request_duration_seconds_total{{{labels}}} {self.request_duration[(method, path)]:.6f}")
            lines.append(f"http_errors_total{{{labels}}} {self.error_count[(method, path)]}")
        for name, value in sorted(self.counters.items()):
            lines.append(f"{name} {value}")
        for name, value in sorted(self.gauges.items()):
            lines.append(f"{name} {value}")
        return "\n".join(lines) + "\n"


metrics = MetricsCollector()


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            route = request.scope.get("route")
            path = getattr(route, "path", request.url.path)
            metrics.record_request(request.method, path, status_code, time.perf_counter() - started)


def metrics_endpoint(service_name: str):
    async def handler(request: Request):
        return PlainTextResponse(metrics.render(service_name), media_type="text/plain; version=0.0.4")

    return handler
