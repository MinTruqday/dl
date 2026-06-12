import httpx
import time
from fastapi import HTTPException
from loguru import logger

class CircuitBreaker:
    def __init__(self, max_failures=5, reset_timeout=60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def check(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise HTTPException(status_code=503, detail="AI đang bảo trì")
                
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
        
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.state = "OPEN"
            logger.warning("Circuit Breaker OPEN: Dịch vụ AI đang bị ngắt kết nối tạm thời do lỗi liên tục")

ai_circuit_breaker = CircuitBreaker()

ai_http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
    timeout=httpx.Timeout(30.0)
)

async def make_ai_request(url: str, json_data: dict, timeout: float = 30.0):
    ai_circuit_breaker.check()
    try:
        response = await ai_http_client.post(url, json=json_data, timeout=timeout)
        response.raise_for_status()
        ai_circuit_breaker.on_success()
        return response
    except Exception as e:
        ai_circuit_breaker.on_failure()
        raise e

