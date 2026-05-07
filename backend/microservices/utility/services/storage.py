import uuid
from fastapi import HTTPException
from core.storage import generate_presigned_url, upload_file
from loguru import logger
class StorageService:
    @staticmethod
    async def upload_asset(file, current_user):
        ext = file.filename.split(".")[-1]
        filename = f"assets/{current_user.id}/{uuid.uuid4().hex}.{ext}"
        content = await file.read()
        await upload_file(content, filename, file.content_type)
        logger.info(f"Asset uploaded by user {current_user.id}: {filename}")
        return {"url": filename, "filename": filename}
    @staticmethod
    async def get_presigned_url(file_path: str):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Đường dẫn tệp không hợp lệ.")
        url = await generate_presigned_url(file_path, 3600)
        return {"download_url": url}
