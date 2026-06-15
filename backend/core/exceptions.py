from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

class GlobalExceptionHandler:
    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception):
        logger.warning("Incoming client payload explicitly violated strictly defined structural validation schema parameters")
        return JSONResponse(
            status_code=422,
            content={"message": "Submitted operational request payload violates explicitly defined structural validation formatting parameters"}
        )

    @staticmethod
    async def handle_internal_error(request: Request, exc: Exception):
        logger.error("Internal processing matrix encountered an unexpected unhandled operational computational exception")
        return JSONResponse(
            status_code=500,
            content={"message": "System encountered an unexpected critical structural failure requiring immediate administrative intervention"}
        )

    @staticmethod
    async def handle_not_found(request: Request, exc: Exception):
        logger.warning("Requested operational routing endpoint destination remains utterly untraceable within active system architecture")
        return JSONResponse(
            status_code=404,
            content={"message": "Specifically designated operational network endpoint could not be successfully located internally"}
        )

def setup_global_exceptions(app):
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(RequestValidationError, GlobalExceptionHandler.handle_validation_error)
    app.add_exception_handler(Exception, GlobalExceptionHandler.handle_internal_error)
    app.add_exception_handler(StarletteHTTPException, GlobalExceptionHandler.handle_not_found)