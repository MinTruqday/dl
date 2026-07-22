import time
import json
from typing import Callable, Any
from fastapi import Request, Response
from fastapi.routing import APIRoute
from loguru import logger

def mask_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        masked_data = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ['password', 'token', 'secret', 'key', 'authorization']):
                masked_data[k] = "***"
            else:
                masked_data[k] = mask_sensitive_data(v)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data

class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            body = await request.body()
            body_str = ""
            if body:
                try:
                    payload = json.loads(body)
                    masked_payload = mask_sensitive_data(payload)
                    body_str = json.dumps(masked_payload, ensure_ascii=False)[:500]
                except (ValueError, UnicodeDecodeError):
                    body_str = body.decode('utf-8', errors='ignore')[:500]
            
            query = str(request.query_params)
            logger.info(f"API Request Started for {request.method} {request.url.path} with Query {query} and Body {body_str}")
            
            start_time = time.time()
            try:
                response: Response = await original_route_handler(request)
                process_time = time.time() - start_time
                logger.info(f"API Request Completed for {request.method} {request.url.path} with Status {response.status_code} in {process_time:.3f}s")
                return response
            except Exception as e:
                process_time = time.time() - start_time
                logger.exception(f"Unexpected system error while processing API request {request.method} {request.url.path} after {process_time:.3f}s")
                raise e

        return custom_route_handler
