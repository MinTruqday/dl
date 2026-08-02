import os
import uuid

from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.logic_logger import log_logic_execution
from src.core.storage import generate_presigned_url, upload_file


class UploadService:
    allowed_extensions = {
        "pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "zip",
        "csv", "json", "md", "png", "jpg", "jpeg", "webp", "webm", "doclib",
        "doclibx",
    }
    image_extensions = {"png", "jpg", "jpeg", "webp"}

    @staticmethod
    def validate_filename(filename: str, content_type: str, image_only: bool = False) -> str:
        if not filename or filename != os.path.basename(filename) or filename in {".", ".."}:
            raise HTTPException(status_code=400, detail="Tên tệp không hợp lệ")
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed = UploadService.image_extensions if image_only else UploadService.allowed_extensions
        if ext not in allowed or ext == "svg" or "svg" in content_type.lower():
            raise HTTPException(status_code=400, detail="Định dạng tệp tin không được hỗ trợ")
        if image_only and not content_type.lower().startswith("image/"):
            raise HTTPException(status_code=400, detail="Định dạng hình ảnh không hợp lệ")
        return ext

    @staticmethod
    async def read_limited(file) -> bytes:
        content = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
        if not content:
            raise HTTPException(status_code=400, detail="Tệp tải lên không được để trống")
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Tệp tải lên vượt quá kích thước cho phép")
        return content

    @staticmethod
    def object_path(ext: str, content_type: str, owner_id: str | None, is_system: bool, is_message_attachment: bool, is_temporary: bool = False) -> str:
        kind = "images" if content_type.lower().startswith("image/") else "documents"
        if is_system:
            return f"system/{kind}/{uuid.uuid4().hex}.{ext}"
        if owner_id and is_temporary:
            return f"temp/{owner_id}/{uuid.uuid4().hex}.{ext}"
        if owner_id:
            folder = "message_attachments" if is_message_attachment else kind
            return f"users/{owner_id}/{folder}/{uuid.uuid4().hex}.{ext}"
        return f"public/{kind}/{uuid.uuid4().hex}.{ext}"

    @staticmethod
    @log_logic_execution
    async def upload_image(file, owner_id: str | None = None, is_system: bool = False):
        content_type = file.content_type or "application/octet-stream"
        ext = UploadService.validate_filename(file.filename, content_type, True)
        content = await UploadService.read_limited(file)
        path = UploadService.object_path(ext, content_type, owner_id, is_system, False)
        try:
            await upload_file(content, path, content_type)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Image storage operation failed")
            raise HTTPException(status_code=500, detail="Không thể lưu trữ tệp hình ảnh")
        return {"url": path, "filename": file.filename, "size": len(content), "content_type": content_type}

    @staticmethod
    @log_logic_execution
    async def upload_document(file, owner_id: str | None = None, is_system: bool = False, is_message_attachment: bool = False, is_temporary: bool = False):
        content_type = file.content_type or "application/octet-stream"
        ext = UploadService.validate_filename(file.filename, content_type)
        content = await UploadService.read_limited(file)
        path = UploadService.object_path(ext, content_type, owner_id, is_system, is_message_attachment, is_temporary)
        try:
            await upload_file(content, path, content_type)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Document storage operation failed")
            raise HTTPException(status_code=500, detail="Không thể lưu trữ tài liệu")
        return {"url": path, "filename": file.filename, "extension": ext, "size": len(content), "content_type": content_type}

    @staticmethod
    @log_logic_execution
    async def get_presigned_url(file_path: str):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Đường dẫn tệp tin không hợp lệ")
        try:
            return {"download_url": await generate_presigned_url(file_path, 3600)}
        except Exception:
            logger.exception("Failed to generate presigned download URL")
            raise HTTPException(status_code=500, detail="Không thể khởi tạo liên kết tải xuống")

    @staticmethod
    @log_logic_execution
    async def get_presigned_upload_url(filename: str, content_type: str, owner_id: str, is_system: bool = False, is_message_attachment: bool = False, is_temporary: bool = False):
        from src.core.storage import generate_presigned_put_url

        ext = UploadService.validate_filename(filename, content_type)
        path = UploadService.object_path(ext, content_type, owner_id, is_system, is_message_attachment, is_temporary)
        try:
            url = await generate_presigned_put_url(path, content_type, 3600)
            return {"upload_url": url, "file_path": path}
        except Exception:
            logger.exception("Failed to generate presigned upload URL")
            raise HTTPException(status_code=500, detail="Không thể khởi tạo liên kết tải lên")
