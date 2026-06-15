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
    logger.info("Structured internal operational logging engine successfully initialized processing automated formatting streams")