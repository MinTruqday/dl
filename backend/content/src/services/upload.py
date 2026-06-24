import uuid

from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from shared.storage import generate_presigned_url, upload_file


class UploadService:

    @staticmethod
    async def upload_image(file, db=None):
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
        filename = f"images/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f"Lỗi lưu hình ảnh: {e}")
            raise HTTPException(
                status_code=500, detail=f"Lỗi truyền tệp hình ảnh vào bộ nhớ vĩnh viễn: {e}"
            )
        return {
            "url": filename,
            "filename": filename,
            "message": "Tải lên hình ảnh lưu trữ thành công",
        }

    @staticmethod
    async def upload_document(file, db=None):
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
        filename = f"documents/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f"Lỗi mạng khi lưu trữ tài liệu: {e}")
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
    async def get_presigned_url(file_path: str, db=None):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(
                status_code=400, detail="Đường dẫn tệp tin không hợp lệ"
            )
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {"download_url": url}
        except Exception as e:
            logger.error(f"Lỗi tạo liên kết tải xuống bảo mật: {e}")
            raise HTTPException(
                status_code=500, detail=f"Lỗi tạo liên kết truy cập bảo mật: {e}"
            )
