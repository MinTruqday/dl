import asyncio
import hashlib
import os
import re
import shutil
import urllib.parse

import aiohttp
import img2pdf
from loguru import logger
from playwright.async_api import Response, async_playwright
from src.infrastructure.browser import get_stealth_context, managed_browser
from src.core.database import database
from src.core.cache import dedup
from src.core.storage import storage
from src.services.metadata import collected_metadata
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings

MIN_FILE_SIZE_BYTES = settings.MIN_FILE_SIZE_BYTES


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
                        content_hash = hashlib.md5(body).hexdigest()

                        if content_hash in self.captured_hashes:
                            return

                        ext = ".jpg"
                        if "png" in url.lower() or "png" in content_type:
                            ext = ".png"

                        filename = f"nxbgd_page_{self.page_counter:03d}{ext}"
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
        slug = urllib.parse.quote(title.lower().replace(" ", "-"), safe="")[:50]
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
            logger.warning("[NXBGD] Skipping PDF compilation due to lack of valid captured images")
            return

        try:
            logger.info("[NXBGD] Compiling captured images into PDF document")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(image_files))
            logger.info("[NXBGD] PDF compilation and temporary storage successful")

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
                return await database.insert_document(metadata)

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

    async def execute(self, job_id: str | None = None):
        await self.init_browser()

        url = f"https://taphuan.nxbgd.vn/tap-huan?grade={self.target_class}"
        documents_detected = 0
        documents_saved = 0
        failed_items = 0
        pages_scanned = 0
        try:
            logger.info("[NXBGD] Accessing root domain for category scraping")
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(5)

            has_next = True

            while has_next:
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
                    full_doc_url = (
                        f"https://taphuan.nxbgd.vn{doc_url}" if doc_url.startswith("/") else doc_url
                    )
                    self.source_url = full_doc_url
                    logger.info("[NXBGD] Retrieving detailed document information")

                    try:
                        await self.page.goto(full_doc_url, timeout=60000)
                        await asyncio.sleep(4)

                        doc_links = await self.page.query_selector_all("a[href*='/doc-sach/']")
                        if not doc_links:
                            continue

                        for doc_link in doc_links:
                            res_name = await doc_link.text_content()
                            res_name = res_name.strip()
                            full_title = res_name

                            if await dedup.is_collected("taphuan_book", full_title):
                                logger.info("[NXBGD] Skipping already processed document")
                                continue

                            await dedup.mark_collected("taphuan_book", full_title)

                            viewer_url = await doc_link.get_attribute("href")
                            if viewer_url.startswith("/"):
                                viewer_url = f"https://taphuan.nxbgd.vn{viewer_url}"

                            logger.info("[NXBGD] Preparing to process detailed document content")

                            safe_title = re.sub(r'[\\/*?:"<>|]', "", full_title).strip()
                            import tempfile

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
                            document_id = await self.compile_and_upload(full_title)
                            if document_id:
                                documents_saved += 1
                            else:
                                failed_items += 1
                            await viewer_page.close()
                    except Exception:
                        failed_items += 1
                        logger.exception("[NXBGD] Document information extraction failed")

                try:
                    await self.page.goto(url, timeout=60000)
                    await asyncio.sleep(5)
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

                break

            return {
                "pages_scanned": pages_scanned,
                "documents_detected": documents_detected,
                "documents_queued": documents_saved + failed_items,
                "documents_completed": documents_saved,
                "failed_items": failed_items,
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
