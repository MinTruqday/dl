from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

class GlobalExceptionHandler:
    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception):
        logger.warning("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return JSONResponse(
            status_code=422,
            content={"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
        )

    @staticmethod
    async def handle_internal_error(request: Request, exc: Exception):
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return JSONResponse(
            status_code=500,
            content={"message": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}
        )

    @staticmethod
    async def handle_not_found(request: Request, exc: Exception):
        logger.warning("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return JSONResponse(
            status_code=404,
            content={"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}
        )

def setup_global_exceptions(app):
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(RequestValidationError, GlobalExceptionHandler.handle_validation_error)
    app.add_exception_handler(Exception, GlobalExceptionHandler.handle_internal_error)
    app.add_exception_handler(StarletteHTTPException, GlobalExceptionHandler.handle_not_found)