import uuid

from core.storage import generate_presigned_url, upload_file
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class UploadService:

    @staticmethod
    async def upload_image(file, db=None):
        if "svg" in file.content_type.lower() or file.filename.lower().endswith(".svg"):
            raise HTTPException(status_code=400, detail="SVG format is not supported")
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="Only image files are supported"
            )
        ext = file.filename.split("")[-1]
        filename = f"images/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error("Failed to upload image")
            raise HTTPException(status_code=500, detail="Failed to upload image")
        return {
            "url": filename,
            "filename": filename,
            "message": "Image uploaded successfully",
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
                status_code=400, detail="SVG file upload is not allowed"
            )
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Format .{ext} is not supported")
        filename = f"documents/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error("Failed to upload document")
            raise HTTPException(status_code=500, detail="Failed to upload document")
        return {
            "url": filename,
            "filename": filename,
            "extension": ext,
            "message": "Document uploaded successfully",
        }

    @staticmethod
    async def get_presigned_url(file_path: str, db=None):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path provided")
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {"download_url": url}
        except Exception as e:
            logger.error("Failed to generate download link")
            raise HTTPException(
                status_code=500, detail="Failed to generate download link"
            )
