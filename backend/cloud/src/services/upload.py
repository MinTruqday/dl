import uuid

from src.core.logic_logger import log_logic_execution
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.core.storage import generate_presigned_url, upload_file

class UploadService:

    @staticmethod
    @log_logic_execution
    async def upload_image(file, owner_id: str = None, is_system: bool = False):
        if "svg" in file.content_type.lower() or file.filename.lower().endswith(".svg"):
            raise HTTPException(
                status_code=400, detail="Không hỗ trợ định dạng hình ảnh vector này"
            )
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Chỉ chấp nhận các định dạng hình ảnh tiêu chuẩn",
            )
        ext = file.filename.split(".")[-1]
        
        if is_system:
            filename = f"system/images/{uuid7().hex}.{ext}"
        elif owner_id:
            filename = f"users/{owner_id}/message_attachments/{uuid7().hex}.{ext}"
        else:
            filename = f"public/images/{uuid7().hex}.{ext}"
            
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.exception("Lỗi lưu trữ hình ảnh")
            raise HTTPException(
                status_code=500, detail=f"Lỗi truyền tệp hình ảnh vào bộ nhớ vĩnh viễn: {e}"
            )
        return {
            "url": filename,
            "filename": filename,
            "message": "Tải lên hình ảnh lưu trữ thành công",
        }

    @staticmethod
    @log_logic_execution
    async def upload_document(file, owner_id: str = None, is_system: bool = False, is_message_attachment: bool = False):
        allowed_extensions = [
            "pdf",
            "epub",
            "mobi",
            "docx",
            "doc",
            "xlsx",
            "xls",
            "pptx",
            "ppt",
            "txt",
            "zip",
            "csv",
            "json",
            "md",
            "png",
            "jpg",
            "jpeg",
            "webp",
            "webm",
            "mp3",
            "wav",
            "m4a",
            "ogg",
            "mp4",
        ]
        ext = file.filename.split(".")[-1].lower()
        if ext == "svg" or "svg" in file.content_type.lower():
            raise HTTPException(
                status_code=400, detail="Không hỗ trợ định dạng hình ảnh vector này"
            )
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, detail="Định dạng tệp không được hỗ trợ"
            )
            
        if is_system:
            filename = f"system/documents/{uuid7().hex}.{ext}"
        elif owner_id:
            folder = "message_attachments" if is_message_attachment else "documents"
            filename = f"users/{owner_id}/{folder}/{uuid7().hex}.{ext}"
        else:
            filename = f"public/documents/{uuid7().hex}.{ext}"
            
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.exception("Lỗi mạng trong quá trình lưu trữ tài liệu")
            raise HTTPException(
                status_code=500, detail=f"Lỗi lưu trữ, không thể tải lên tài liệu: {e}"
            )
        return {
            "url": filename,
            "filename": filename,
            "extension": ext,
            "message": "Tải lên tài liệu thành công",
        }

    @staticmethod
    @log_logic_execution
    async def get_presigned_url(file_path: str):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(
                status_code=400, detail="Đường dẫn tệp tin không hợp lệ"
            )
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {"download_url": url}
        except Exception as e:
            logger.exception("Lỗi tạo đường dẫn tải xuống bảo mật")
            raise HTTPException(
                status_code=500, detail=f"Lỗi tạo liên kết truy cập bảo mật: {e}"
            )

    @staticmethod
    @log_logic_execution
    async def get_presigned_upload_url(filename: str, content_type: str, owner_id: str = None, is_system: bool = False, is_message_attachment: bool = False):
        from src.core.storage import generate_presigned_put_url
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        if is_system:
            folder_type = "images" if content_type.startswith("image/") else "documents"
            file_path = f"system/{folder_type}/{uuid7().hex}.{ext}"
        elif owner_id:
            if is_message_attachment:
                folder = "message_attachments"
            else:
                folder = "images" if content_type.startswith("image/") else "documents"
            file_path = f"client/{owner_id}/{folder}/{uuid7().hex}.{ext}"
        else:
            folder_type = "images" if content_type.startswith("image/") else "documents"
            file_path = f"public/{folder_type}/{uuid7().hex}.{ext}"
            
        try:
            url = await generate_presigned_put_url(file_path, content_type, 3600)
            return {"upload_url": url, "file_path": file_path}
        except Exception as e:
            logger.exception("Lỗi tạo đường dẫn tải lên bảo mật")
            raise HTTPException(
                status_code=500, detail=f"Lỗi tạo liên kết tải lên: {e}"
            )
