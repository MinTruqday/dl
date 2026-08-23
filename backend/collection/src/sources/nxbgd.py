import asyncio
import hashlib
import os
import re
import shutil
import uuid
from io import BytesIO

import aiohttp
import img2pdf
from loguru import logger
from PIL import Image
from playwright.async_api import Response
from src.infrastructure.browser import get_stealth_context, managed_browser
from src.core.database import database
from src.core.cache import dedup
from src.core.storage import storage
from src.core.infrastructure.redis import redis
from src.services.metadata import collected_metadata

from src.core.infrastructure.configuration import settings

MIN_FILE_SIZE_BYTES = settings.MIN_FILE_SIZE_BYTES


def page_number_from_url(url: str) -> int | None:
    for pattern in [r"(?:page|trang|pageno)[=_/-]?(\d{1,5})", r"/(\d{1,5})\.(?:jpg|jpeg|png)(?:\?|$)"]:
        match = re.search(pattern, url, re.I)
        if match:
            return int(match.group(1))
    return None


class NxbgdSource:
    def __init__(self, target_class: str):
        self.target_class = target_class
        self.page = None
        self.context = None
        self.browser = None
        self.temp_dir = ""
        self.is_capturing = False
        self.captured_hashes = set()
        self.page_counter = 0
        self.duplicate_pages = 0
        self.suspicious_pages = 0
        self.capture_lock = asyncio.Lock()
        self.source_url = None

    async def _handle_response(self, response: Response):
        if not self.is_capturing or not self.temp_dir:
            return

        try:
            url = response.url
            content_type = response.headers.get("content-type", "")

            if "image" in content_type or any(
                ext in url.lower() for ext in [".jpg", ".jpeg", ".png"]
            ):
                if any(
                    skip in url for skip in ["icon", "avatar", "logo", "button", "blank_book_page"]
                ):
                    return

                try:
                    body = await response.body()
                    if len(body) > MIN_FILE_SIZE_BYTES:
                        with Image.open(BytesIO(body)) as candidate:
                            width, height = candidate.size
                            extrema = candidate.convert("L").resize((64, 64)).getextrema()
                        if width < 400 or height < 400 or extrema[1] - extrema[0] < 3:
                            self.suspicious_pages += 1
                            return
                        content_hash = hashlib.sha256(body).hexdigest()

                        ext = ".jpg"
                        if "png" in url.lower() or "png" in content_type:
                            ext = ".png"

                        async with self.capture_lock:
                            if content_hash in self.captured_hashes:
                                self.duplicate_pages += 1
                                return
                            source_page = page_number_from_url(url)
                            ordering = source_page if source_page is not None else self.page_counter
                            filename = f"nxbgd_page_{ordering:05d}_{self.page_counter:05d}{ext}"
                            save_path = os.path.join(self.temp_dir, filename)
                            with open(save_path, "wb") as f:
                                f.write(body)
                            logger.info("[NXBGD] Document page captured and saved")
                            self.captured_hashes.add(content_hash)
                            self.page_counter += 1
                except Exception as e:
                    logger.exception("[NXBGD] Page image download failed")
        except Exception as e:
            logger.exception("[NXBGD] Network response analysis failed")

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

    async def compile_and_upload(self, title: str, author: str = ""):
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        final_pdf_name = f"{safe_title}_{uuid.uuid4().hex[:12]}.pdf"

        pdf_path = os.path.join(self.temp_dir, final_pdf_name)

        image_files = sorted(
            [
                os.path.join(self.temp_dir, f)
                for f in os.listdir(self.temp_dir)
                if f.startswith("nxbgd_page_") and (f.endswith(".jpg") or f.endswith(".png"))
            ]
        )

        if not image_files:
            logger.warning("[NXBGD] Skipping PDF compilation due to lack of valid captured images")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            return

        try:
            normalized_images = []
            for index, image_path in enumerate(image_files):
                normalized_path = os.path.join(self.temp_dir, f"nxbgd_pdf_{index:03d}.jpg")
                with Image.open(image_path) as image:
                    image.convert("RGB").save(normalized_path, "JPEG")
                normalized_images.append(normalized_path)
            logger.info("[NXBGD] Compiling captured images into PDF document")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(normalized_images))
            logger.info("[NXBGD] PDF compilation and temporary storage successful")

            with open(pdf_path, "rb") as stream:
                content_hash = hashlib.sha256(stream.read()).hexdigest()
            if await dedup.is_collected("nxbgd_content", content_hash):
                return "existing"

            logger.info("[NXBGD] Uploading compiled document to permanent storage")
            minio_url = await storage.upload_local_file(
                f"system/collection/nxbgd/{final_pdf_name}", pdf_path
            )

            if minio_url:
                metadata = await collected_metadata(
                    {
                        "title": title,
                        "author": author,
                        "source_url": self.source_url,
                        "content_hash": content_hash,
                        "collection_scope": {
                            "type": "grade",
                            "value": self.target_class,
                        },
                    },
                    pdf_path,
                    minio_url,
                    "pdf",
                    "Nhà Xuất bản Giáo dục Việt Nam",
                    "nxbgd",
                )
                document_id = await database.insert_document(metadata)
                await dedup.mark_collected("nxbgd_content", content_hash)
                await dedup.mark_collected("nxbgd_url", self.source_url)
                return document_id

        except Exception as e:
            logger.exception("[NXBGD] Document compilation or upload failed")
            raise
        finally:
            logger.info("[NXBGD] Cleaning up temporary data directories")
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.exception("[NXBGD] Permission error during temporary file cleanup")

    @staticmethod
    async def probe_list_source() -> dict:
        url = "https://taphuan.nxbgd.vn/tap-huan?grade=1"
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    body = await response.text(errors="ignore")
                    detected = len(
                        set(re.findall(r'href=["\']([^"\']*/chi-tiet-sach/[^"\']+)', body))
                    )
                    reachable = response.status == 200 and detected > 0
                    return {
                        "source": "NXBGD",
                        "reachable": reachable,
                        "http_status": response.status,
                        "documents_detected": detected,
                        "reason": None if reachable else "Source returned no document records",
                    }
        except Exception as error:
            return {
                "source": "NXBGD",
                "reachable": False,
                "http_status": None,
                "documents_detected": 0,
                "reason": str(error)[:200],
            }

    async def execute(self, job_id: str | None = None, max_documents: int = 1, force_recrawl: bool = False):
        await self.init_browser()

        url = f"https://taphuan.nxbgd.vn/tap-huan?grade={self.target_class}"
        documents_detected = 0
        documents_saved = 0
        failed_items = 0
        duplicate_items = 0
        duplicate_pages_total = 0
        suspicious_pages_total = 0
        pages_scanned = 0
        cancelled = False
        try:
            logger.info("[NXBGD] Accessing root domain for category scraping")
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(5)

            has_next = True

            while has_next and documents_saved + failed_items + duplicate_items < max_documents:
                if await redis.get("stop_collection") == "1" or job_id and await redis.get(f"collection:cancel:{job_id}") == "1":
                    cancelled = True
                    break
                pages_scanned += 1
                document_elements = await self.page.query_selector_all("a[href*='/chi-tiet-sach/']")
                document_urls = []
                for b in document_elements:
                    href = await b.get_attribute("href")
                    if href and href not in document_urls:
                        document_urls.append(href)

                logger.info("[NXBGD] Found document elements on category page")
                documents_detected += len(document_urls)

                for doc_url in document_urls:
                    if cancelled:
                        break
                    if documents_saved + failed_items + duplicate_items >= max_documents:
                        break
                    full_doc_url = (
                        f"https://taphuan.nxbgd.vn{doc_url}" if doc_url.startswith("/") else doc_url
                    )
                    self.source_url = full_doc_url
                    logger.info("[NXBGD] Retrieving detailed document information")

                    detail_page = None
                    viewer_page = None
                    try:
                        detail_page = await self.context.new_page()
                        await detail_page.goto(full_doc_url, timeout=60000)
                        await asyncio.sleep(4)

                        doc_links = await detail_page.query_selector_all("a[href*='/doc-sach/']")
                        if not doc_links:
                            continue

                        for doc_link in doc_links:
                            if documents_saved + failed_items + duplicate_items >= max_documents:
                                break
                            res_name = str(await doc_link.text_content() or "").strip()
                            if not res_name:
                                failed_items += 1
                                continue
                            full_title = res_name

                            viewer_url = await doc_link.get_attribute("href")
                            if not viewer_url:
                                failed_items += 1
                                continue
                            if viewer_url.startswith("/"):
                                viewer_url = f"https://taphuan.nxbgd.vn{viewer_url}"
                            self.source_url = viewer_url

                            if not force_recrawl and await dedup.is_collected("nxbgd_url", viewer_url):
                                logger.info("[NXBGD] Skipping already processed document")
                                duplicate_items += 1
                                continue

                            logger.info("[NXBGD] Preparing to process detailed document content")

                            safe_title = re.sub(r'[\\/*?:"<>|]', "", full_title).strip()
                            import tempfile

                            self.temp_dir = tempfile.mkdtemp(prefix=f"nxbgd_{safe_title[:20]}_")
                            os.makedirs(self.temp_dir, exist_ok=True)

                            self.captured_hashes = set()
                            self.page_counter = 0
                            self.duplicate_pages = 0
                            self.suspicious_pages = 0
                            self.is_capturing = True

                            viewer_page = await self.context.new_page()
                            viewer_page.on("response", self._handle_response)
                            await viewer_page.goto(viewer_url, timeout=60000)
                            await asyncio.sleep(5)

                            last_page_count = 0
                            stable_count = 0
                            for _ in range(150):
                                if await redis.get("stop_collection") == "1" or job_id and await redis.get(f"collection:cancel:{job_id}") == "1":
                                    cancelled = True
                                    break
                                try:
                                    next_btn = await viewer_page.query_selector(
                                        "button i.fa-angle-right"
                                    )
                                    if next_btn:
                                        await next_btn.click()
                                    else:
                                        await viewer_page.keyboard.press("PageDown")
                                        await viewer_page.keyboard.press("Space")
                                except Exception as e:
                                    logger.exception("[NXBGD] Document viewer interaction failed")
                                await asyncio.sleep(2)

                                current_pages = len(self.captured_hashes)
                                if current_pages > 0 and current_pages == last_page_count:
                                    stable_count += 1
                                    if stable_count >= 4:
                                        logger.info("[NXBGD] Document scanning completed")
                                        break
                                else:
                                    stable_count = 0
                                last_page_count = current_pages

                            self.is_capturing = False
                            duplicate_pages_total += self.duplicate_pages
                            suspicious_pages_total += self.suspicious_pages
                            if cancelled:
                                await viewer_page.close()
                                viewer_page = None
                                shutil.rmtree(self.temp_dir, ignore_errors=True)
                                break
                            document_id = await self.compile_and_upload(full_title)
                            if document_id == "existing":
                                duplicate_items += 1
                            elif document_id:
                                documents_saved += 1
                            else:
                                failed_items += 1
                            await viewer_page.close()
                            viewer_page = None
                            if cancelled or documents_saved + failed_items + duplicate_items >= max_documents:
                                break
                    except Exception:
                        failed_items += 1
                        logger.exception("[NXBGD] Document information extraction failed")
                    finally:
                        self.is_capturing = False
                        if self.temp_dir and os.path.isdir(self.temp_dir):
                            shutil.rmtree(self.temp_dir, ignore_errors=True)
                        pages_to_close = [page for page in [viewer_page, detail_page] if page]
                        if pages_to_close:
                            await asyncio.gather(*(page.close() for page in pages_to_close), return_exceptions=True)

                if cancelled:
                    break
                try:
                    next_btn = await self.page.query_selector("button.p-paginator-next")
                    if (
                        next_btn
                        and not await next_btn.is_disabled()
                        and "p-disabled" not in (await next_btn.get_attribute("class") or "")
                    ):
                        logger.info("[NXBGD] Loading next page of document list")
                        await next_btn.click()
                        await asyncio.sleep(4)
                    else:
                        has_next = False
                        logger.info("[NXBGD] Reached the last page of document list")
                except Exception as e:
                    logger.exception("[NXBGD] Automatic pagination failed")
                    has_next = False

            return {
                "pages_scanned": pages_scanned,
                "documents_detected": documents_detected,
                "documents_queued": documents_saved + failed_items + duplicate_items,
                "documents_completed": documents_saved,
                "failed_items": failed_items,
                "duplicate_items": duplicate_items,
                "duplicate_pages": duplicate_pages_total,
                "suspicious_pages": suspicious_pages_total,
                "cancelled": cancelled,
            }

        except Exception as e:
            logger.exception("[NXBGD] Redirection error during source data collection")
            raise
        finally:
            await self.close()


async def run_nxbgd_collector(target_class: str, job_id: str | None = None):
    logger.info("[NXBGD] Initializing data collection pipeline")
    collector = NxbgdSource(target_class=target_class)
    return await collector.execute(job_id)
