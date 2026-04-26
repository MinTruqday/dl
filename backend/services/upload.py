import os
import uuid
import shutil
from fastapi import HTTPException
from core.storage import generate_presigned_url
from loguru import logger

UPLOAD_DIR = "public/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadService:
    @staticmethod
    async def upload_image(file):
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Chỉ chấp nhận tệp hình ảnh.")
            
        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_location = os.path.join(UPLOAD_DIR, filename)
        
        try:
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            logger.info(f"Image uploaded: {filename}")
            return {"url": f"/uploads/{filename}", "filename": filename}
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            raise HTTPException(status_code=500, detail="Không thể tải ảnh lên.")

    @staticmethod
    async def get_presigned_url(file_path: str):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Đường dẫn tệp không hợp lệ.")
            
        url = await generate_presigned_url(file_path, 3600)
        return {"download_url": url}
