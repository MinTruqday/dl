import uuid

from core.storage import generate_presigned_url, upload_file
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class UploadService:

    @staticmethod
    async def upload_image(file, db=None):
        if "svg" in file.content_type.lower() or file.filename.lower().endswith(".svg"):
            raise HTTPException(status_code=400, detail="The uploaded vector graphic format is explicitly restricted by the system security policies")
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="The upload operation was rejected because the system currently only accepts standard image file formats"
            )
        ext = file.filename.split(".")[-1]
        filename = f"images/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error("The object storage service encountered an unexpected disruption while attempting to save the image file")
            raise HTTPException(status_code=500, detail="The system was unable to securely transfer the image file to the permanent storage backend")
        return {
            "url": filename,
            "filename": filename,
            "message": "The visual asset has been successfully uploaded and securely stored in the remote repository",
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
                status_code=400, detail="The uploaded vector graphic format is explicitly restricted by the system security policies"
            )
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="The provided file extension is not currently recognized or supported by the document parsing engine")
        filename = f"documents/{uuid7().hex}.{ext}"
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error("The object storage service encountered a network failure while attempting to persist the document file")
            raise HTTPException(status_code=500, detail="The system encountered an internal storage failure and could not successfully upload the document")
        return {
            "url": filename,
            "filename": filename,
            "extension": ext,
            "message": "The digital document has been successfully uploaded and integrated into the storage workspace",
        }

    @staticmethod
    async def get_presigned_url(file_path: str, db=None):
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="The provided structural file path is invalid or contains restricted navigational sequences")
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {"download_url": url}
        except Exception as e:
            logger.error("The system encountered an error while attempting to generate a cryptographically signed download URL")
            raise HTTPException(
                status_code=500, detail="The system was unable to successfully generate the secure access link for the requested resource"
            )