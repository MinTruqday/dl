import asyncio
from core.storage import storage
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
        logger.info(f"[Converter] {filename} is already a PDF. requires no conversion.")
        try:
            from src.core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": file_url})
        except ImportError:
            from core.db import db_client
            await db_client.update_document(document_id, {"pdf_url": file_url})
        return

    logger.info(f"[Converter] Analyzing {filename} to build PDF via Calibre.")
    
    import tempfile
    import shutil
    
    try:
        with tempfile.TemporaryDirectory(prefix="converter_") as tmp_dir:
            input_path = os.path.join(tmp_dir, filename)
            pdf_filename = f"{base_name}.pdf"
            pdf_path = os.path.join(tmp_dir, pdf_filename)
            
            async with aiohttp.ClientSession() as s:
                async with s.get(file_url) as r:
                    data = await r.read()
                    with open(input_path, "wb") as f:
                        f.write(data)
                        
            logger.info(f"[Calibre Subprocess]: Starting render of {pdf_path}")
            process = await asyncio.create_subprocess_exec(
                "ebook-convert", input_path, pdf_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"[Calibre Convert Failed]: {stderr.decode()}")
                return
                
            minio_url_pdf = await storage.upload_local_file(
                f"documents/converted/{pdf_filename}", 
                pdf_path
            )
            logger.info(f"Process complete! PDF link (Backup): {minio_url_pdf}")
            
            try:
                from src.core.db import db_client
                await db_client.update_document(document_id, {"pdf_url": minio_url_pdf})
            except ImportError:
                from core.db import db_client
                await db_client.update_document(document_id, {"pdf_url": minio_url_pdf})
            
    except Exception as e:
        logger.error(f"[Format Error] {e}")
