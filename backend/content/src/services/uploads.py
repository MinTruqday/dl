from core.storage import generate_presigned_url, upload_file
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class UploadService:
    @staticmethod
    async def upload_image(file, db=None):
        if "svg" in file.content_type.lower() or file.filename.lower().endswith(".svg"): raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        if not file.content_type.startswith("image/"): raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        filename = f"images/{uuid7().hex}.{file.filename.split('.')[-1]}"
        try: await upload_file(await file.read(), filename, file.content_type)
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            raise HTTPException(status_code=500, detail="Mất kết nối mạng tạm thời")
        return {"url": filename, "filename": filename, "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def upload_document(file, db=None):
        ext = file.filename.split(".")[-1].lower()
        if ext == "svg" or "svg" in file.content_type.lower(): raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        if ext not in ["pdf", "epub", "mobi", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "zip", "csv", "json", "md", "png", "jpg", "jpeg", "webp", "webm", "mp3", "wav", "m4a", "ogg", "mp4"]: raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        filename = f"documents/{uuid7().hex}.{ext}"
        try: await upload_file(await file.read(), filename, file.content_type)
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            raise HTTPException(status_code=500, detail="Mất kết nối mạng tạm thời")
        return {"url": filename, "filename": filename, "extension": ext, "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_presigned_url(file_path: str, db=None):
        if ".." in file_path or file_path.startswith("/"): raise HTTPException(status_code=400, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        try: return {"download_url": await generate_presigned_url(file_path, 3600)}
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            raise HTTPException(status_code=500, detail="Mất kết nối mạng tạm thời")