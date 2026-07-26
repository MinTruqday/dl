import time
from typing import Callable
from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from loguru import logger

class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            logger.info(f"API Request Started for {request.method} {request.url.path}")
            start_time = time.time()
            try:
                response: Response = await original_route_handler(request)
                process_time = time.time() - start_time
                logger.info(f"API Request Completed for {request.method} {request.url.path} with Status {response.status_code} in {process_time:.3f}s")
                return response
            except (HTTPException, RequestValidationError):
                process_time = time.time() - start_time
                logger.warning(f"API Request Rejected for {request.method} {request.url.path} after {process_time:.3f}s")
                raise
            except Exception:
                process_time = time.time() - start_time
                logger.exception(f"Unexpected system error while processing API request {request.method} {request.url.path} after {process_time:.3f}s")
                raise

        return custom_route_handler
