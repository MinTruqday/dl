import os
import uuid
import shutil
import asyncio
from fastapi import HTTPException
from core.storage import generate_presigned_url
from loguru import logger
UPLOAD_DIR = "public/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
class UploadService:
    @staticmethod
    async def upload_image(file):
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Hệ thống chỉ chấp nhận các tệp tin hình ảnh.")
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_location = os.path.join(UPLOAD_DIR, filename)
        def save_sync():
            try:
                with open(file_location, "wb+") as file_object:
                    shutil.copyfileobj(file.file, file_object)
                return True
            except Exception as e:
                logger.error(f"Sync image save error: {e}")
                return False
        success = await asyncio.to_thread(save_sync)
        if not success:
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi đang lưu trữ hình ảnh.")
        logger.info(f"Image uploaded: {filename}")
        return {"url": f"/uploads/{filename}", "filename": filename}
    @staticmethod
    async def upload_document(file):
        allowed_extensions = ["pdf", "epub", "mobi", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "zip", "csv", "json", "md", "png", "jpg", "jpeg", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Hệ thống không hỗ trợ định dạng .{ext}")
        filename = f"docs_{uuid.uuid4().hex}.{ext}"
        file_location = os.path.join(UPLOAD_DIR, filename)
        def save_sync():
            try:
                with open(file_location, "wb+") as file_object:
                    shutil.copyfileobj(file.file, file_object)
                return True
            except Exception as e:
                logger.error(f"Sync document save error: {e}")
                return False
        success = await asyncio.to_thread(save_sync)
        if not success:
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi đang lưu trữ tài liệu.")
        logger.info(f"Document uploaded: {filename}")
        return {"url": f"/uploads/{filename}", "filename": filename, "extension": ext}
    @staticmethod
    async def get_presigned_url(file_path: str):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Đường dẫn tệp tin không hợp lệ.")
        url = await generate_presigned_url(file_path, 3600)
        return {"download_url": url}
