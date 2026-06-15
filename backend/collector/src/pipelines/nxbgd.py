import asyncio
import hashlib
import os
import re
import shutil
import tempfile
import urllib.parse
import img2pdf
from loguru import logger
from playwright.async_api import Response
from core.config import settings
from src.core.browser import get_stealth_context, managed_browser
from src.core.db import db_client
from src.core.redis import dedup
from src.core.storage import storage
from uuid6 import uuid7

MIN_FILE_SIZE_BYTES = settings.MIN_FILE_SIZE_BYTES

class NXBGDPipeline:
    def __init__(self, target_class: str):
        self.target_class = target_class
        self.page = None
        self.context = None
        self.browser = None
        self.temp_dir = ""
        self.is_capturing = False
        self.captured_hashes = set()
        self.page_counter = 0

    async def _handle_response(self, response: Response):
        if not self.is_capturing or not self.temp_dir:
            return

        try:
            url = response.url
            content_type = response.headers.get("content-type", "")

            if "image" in content_type or any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png"]):
                if any(skip in url for skip in ["icon", "avatar", "logo", "button", "blank_book_page"]):
                    return

                try:
                    body = await response.body()
                    if len(body) > MIN_FILE_SIZE_BYTES:
                        content_hash = hashlib.md5(body).hexdigest()

                        if content_hash in self.captured_hashes:
                            return

                        ext = ".png" if ("png" in url.lower() or "png" in content_type) else ".jpg"
                        filename = f"nxbgd_page_{self.page_counter:03d}{ext}"
                        save_path = os.path.join(self.temp_dir, filename)

                        with open(save_path, "wb") as f:
                            f.write(body)

                        logger.info("Visual capture module successfully intercepted and saved high resolution structural document page")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception:
                    logger.warning("Visual capture module encountered minor interruption attempting to retrieve page image sequence data")
        except Exception:
            logger.warning("Unexpected error occurred parsing intercepted network response from primary document viewer component")

    async def init_browser(self):
        self._browser_cm = managed_browser()
        self.browser = await self._browser_cm.__aenter__()
        self.context = await get_stealth_context(self.browser)
        self.page = await self.context.new_page()

    async def close(self):
        if self.context:
            await self.context.close()
        if hasattr(self, "_browser_cm"):
            await self._browser_cm.__aexit__(None, None, None)

    async def compile_and_upload(self, title: str):
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        final_pdf_name = f"{safe_title}_{uuid7().hex[:6]}.pdf"

        pdf_path = os.path.join(self.temp_dir, final_pdf_name)

        image_files = sorted(
            [
                os.path.join(self.temp_dir, f)
                for f in os.listdir(self.temp_dir)
                if f.startswith("nxbgd_page_") and (f.endswith(".jpg") or f.endswith(".png"))
            ]
        )

        if not image_files:
            logger.warning("Document compilation process skipped because no valid image pages successfully captured locally")
            return

        try:
            logger.info("Rendering engine actively compiling captured image sequence into unified portable document format")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(image_files))
            logger.info("Unified structural document successfully compiled and saved to local secure temporary workspace")

            logger.info("Compiled structural document securely transferring to permanent distributed object storage backend")
            minio_url = await storage.upload_local_file(f"documents/nxbgd/{final_pdf_name}", pdf_path)

            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Extracted via automated collection process",
                    "file_url": minio_url,
                    "tags": ["Nhà Xuất bản Giáo dục Việt Nam", "Unknown"],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "private",
                    "creator_id": "nxbgd",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0,
                }
                await db_client.insert_document(document_metadata)
        except Exception:
            logger.error("Unexpected system error occurred during final document rendering compilation and upload sequence")
            raise
        finally:
            logger.info("Automated structural cleanup routine securely removing temporary processing directories and asset files")
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                logger.warning("Automated cleanup routine encountered permission access issue removing targeted temporary working files")

    async def execute(self):
        await self.init_browser()
        url = f"https://taphuan.nxbgd.vn/tap-huan?grade={self.target_class}"
        
        try:
            logger.info("Collection bot navigating to primary origin domain to begin categorical scanning process")
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(5)

            has_next = True
            while has_next:
                document_elements = await self.page.query_selector_all("a[href*='/chi-tiet-sach/']")
                document_urls = []
                for b in document_elements:
                    href = await b.get_attribute("href")
                    if href and href not in document_urls:
                        document_urls.append(href)

                logger.info("Scanning module successfully discovered batch of available technical documents on active categorical page")

                for doc_url in document_urls:
                    full_doc_url = f"https://taphuan.nxbgd.vn{doc_url}" if doc_url.startswith("/") else doc_url
                    logger.info("System transitioning to structural details view to extract specific functional metadata profile")

                    try:
                        await self.page.goto(full_doc_url, timeout=60000)
                        await asyncio.sleep(4)

                        doc_links = await self.page.query_selector_all("a[href*='/doc-sach/']")
                        if not doc_links:
                            continue

                        for doc_link in doc_links:
                            res_name = await doc_link.text_content()
                            full_title = res_name.strip()

                            if await dedup.is_collected("taphuan_book", full_title):
                                logger.info("Collection bot skipping current document because it has already been successfully processed")
                                continue

                            await dedup.mark_collected("taphuan_book", full_title)

                            viewer_url = await doc_link.get_attribute("href")
                            if viewer_url.startswith("/"):
                                viewer_url = f"https://taphuan.nxbgd.vn{viewer_url}"

                            logger.info("Active collection module preparing to process detailed graphical contents of target resource")

                            safe_title = re.sub(r'[\\/*?:"<>|]', "", full_title).strip()
                            self.temp_dir = tempfile.mkdtemp(prefix=f"nxbgd_{safe_title[:20]}_")
                            os.makedirs(self.temp_dir, exist_ok=True)

                            self.captured_hashes = set()
                            self.page_counter = 0
                            self.is_capturing = True

                            viewer_page = await self.context.new_page()
                            viewer_page.on("response", self._handle_response)
                            await viewer_page.goto(viewer_url, timeout=60000)
                            await asyncio.sleep(5)

                            last_page_count = 0
                            stable_count = 0
                            for _ in range(150):
                                try:
                                    next_btn = await viewer_page.query_selector("button i.fa-angle-right")
                                    if next_btn:
                                        await next_btn.click()
                                    else:
                                        await viewer_page.keyboard.press("PageDown")
                                        await viewer_page.keyboard.press("Space")
                                except Exception:
                                    logger.warning("Automated navigation script encountered unexpected functional issue interacting with document viewer")
                                await asyncio.sleep(2)

                                current_pages = len(self.captured_hashes)
                                if current_pages > 0 and current_pages == last_page_count:
                                    stable_count += 1
                                    if stable_count >= 4:
                                        logger.info("Visual capture module successfully collected stable functional sequence of document pages")
                                        break
                                else:
                                    stable_count = 0
                                last_page_count = current_pages

                            self.is_capturing = False
                            await self.compile_and_upload(full_title)
                            await viewer_page.close()
                    except Exception:
                        logger.error("System failed to properly inspect document details due to unexpected layout structure timeout")

                try:
                    await self.page.goto(url, timeout=60000)
                    await asyncio.sleep(5)
                    next_btn = await self.page.query_selector("button.p-paginator-next")
                    if next_btn and not await next_btn.is_disabled() and "p-disabled" not in (await next_btn.get_attribute("class") or ""):
                        logger.info("Collection bot executing precise pagination command to access next batch of document listings")
                        await next_btn.click()
                        await asyncio.sleep(4)
                    else:
                        has_next = False
                        logger.info("Scanning sequence reached final structural page or functional pagination controls no longer available")
                except Exception:
                    logger.error("Automated functional pagination script failed navigating to next sequence due to unexpected layout")
                    has_next = False
                break
        except Exception:
            logger.error("Primary structural collection sequence encountered critical functional failure navigating targeted source domain")
            raise
        finally:
            await self.close()