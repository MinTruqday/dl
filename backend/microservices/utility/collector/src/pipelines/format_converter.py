import asyncio
from shared.core.storage import storage
from loguru import logger
import aiohttp
import os
async def run_format_converter(payload: dict):
    document_id = payload.get("document_id")
    file_url = payload.get("file_url")
    filename = payload.get("filename")
    if not file_url or not filename: return
    base_name, ext = os.path.splitext(filename)
    if ext.lower() == '.pdf':
logger.info("Log message sanitized"))
        try:
            from src.core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": file_url})
        except ImportError:
            from shared.core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": file_url})
        return
logger.info("Log message sanitized"))
    input_path = f"/tmp/{filename}"
    pdf_filename = f"{base_name}.pdf"
    pdf_path = f"/tmp/{pdf_filename}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(file_url) as r:
                data = await r.read()
                with open(input_path, "wb") as f:
                    f.write(data)
logger.info("Log message sanitized"))
        process = await asyncio.create_subprocess_exec(
            "ebookconvert", input_path, pdf_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
logger.info("Log message sanitized"))
            return
        minio_url_pdf = await storage.upload_local_file(
            f"documents/{pdf_filename}", 
            pdf_path
        )
logger.info("Log message sanitized"))
        try:
            from src.core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": minio_url_pdf})
        except ImportError:
            from shared.core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": minio_url_pdf})
    except Exception as e:
logger.info("Log message sanitized"))
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
