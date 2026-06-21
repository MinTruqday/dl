import time
from typing import Optional

from loguru import logger


class FaultTolerance:
    def __init__(self, threshold: int, reset_seconds: float):
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._tripped_at: Optional[float] = None

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold and not self._tripped_at:
            self._tripped_at = time.monotonic()
            logger.error("Mất kết nối với máy chủ")

    def record_success(self):
        self._failures = 0
        self._tripped_at = None
