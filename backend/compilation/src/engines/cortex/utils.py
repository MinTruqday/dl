import io
import json
import os
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List
import httpx
from loguru import logger
from uuid6 import uuid7

class CortexUtils:
    @staticmethod
    async def download_image(url: str, temp_dir: str) -> str:
        if not (url.startswith("http://") or url.startswith("https://")):
            return url

        ext = ".png"
        if ".jpg" in url.lower() or ".jpeg" in url.lower():
            ext = ".jpg"
        elif ".gif" in url.lower():
            ext = ".gif"
        elif ".svg" in url.lower():
            ext = ".svg"

        filename = f"img_{uuid7()}{ext}"
        local_path = os.path.join(temp_dir, filename)

        try:
            logger.info("Downloading external image from URL: {}", url)
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    logger.info("Successfully downloaded image to: {}", local_path)
                    return filename
                else:
                    logger.error("Failed to download image from URL. Status: {}", response.status_code)
        except Exception:
            logger.exception("Failed to fetch remote image URL")
        return url

    @staticmethod
    def compile_to_doclibx(content: str, blocks: List[Dict[str, Any]], version: str) -> bytes:
        logger.info("Packaging Cortex document into doclibx bundle")

        words = 0
        title = "Bản thảo chưa đặt tên"
        
        # Check if there is a dedicated title block
        title_block = next((b for b in blocks if b.get("type") == "title"), None)
        if title_block:
            title = title_block.get("content", "").strip()

        for b in blocks:
            if b.get("type") == "paragraph":
                words += len(b.get("content", "").split())
            elif b.get("type") == "h1" and title == "Bản thảo chưa đặt tên":
                title = b.get("content", "").strip()

        reading_time = max(1, words // 200)

        metadata = {
            "compiler": "DocLib Cortex Compiler",
            "version": version,
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "word_count": words,
            "reading_time_minutes": reading_time,
        }

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("main.cortex", content.encode("utf-8"))
            zip_file.writestr(
                "document.json",
                json.dumps(blocks, ensure_ascii=False, indent=2).encode("utf-8"),
            )
            zip_file.writestr(
                "metadata.json",
                json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
            )

        logger.info("Cortex doclibx bundle packaging completed")
        return zip_buffer.getvalue()
