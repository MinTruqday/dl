import sys
from core.middleware import trace_id_filter
from loguru import logger

def setup_production_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        format="{message}",
        filter=trace_id_filter,
        level="INFO",
        serialize=True,
        enqueue=True,
    )
    logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")