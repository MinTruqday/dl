import asyncio
import hashlib
import os
import re
import shutil
import urllib.parse

import aiohttp
import img2pdf
import requests
from loguru import logger
from PIL import Image
from playwright.async_api import Response, async_playwright
from playwright_stealth import stealth_async
from src.infrastructure.browser import get_stealth_context, managed_browser
from src.core.database import database
from src.core.infrastructure.mq import mq as mq_client
from src.core.cache import dedup
from src.core.storage import storage
from src.services.metadata import collected_metadata
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings

MIN_FILE_SIZE_BYTES = settings.MIN_FILE_SIZE_BYTES


class State:
    def __init__(self):
        self.temp_dir = ""
        self.is_capturing = False
        self.captured_hashes = set()
        self.page_counter = 0
        self.source_url = None
        self.collection_scope = None

    async def _handle_response(self, response: Response):
        if not self.is_capturing or not self.temp_dir:
            return

        try:
            url = response.url
            content_type = response.headers.get("content-type", "")

            if (
                "image" in content_type
                or "img.json" in url
                or any(ext in url for ext in [".jpg", ".jpeg", ".png"])
            ):
                if any(
                    skip in url
                    for skip in ["icon", "avatar", "logo", "button", "bg", "banner", "preview.png"]
                ):
                    return

                try:
                    body = await response.body()
                    if len(body) > MIN_FILE_SIZE_BYTES:
                        content_hash = hashlib.md5(body).hexdigest()

                        if content_hash in self.captured_hashes:
                            return

                        match = re.search(r"img_short_(\d+)(\d)", url)
                        if match:
                            page_num = int(match.group(1))
                            tile_num = int(match.group(2))
                            filename = f"nxbst_page_{page_num:04d}_tile{tile_num}.jpg"
                        else:
                            filename = (
                                f"nxbst_page_unknown_{self.page_counter:04d}_{uuid7().hex[:4]}.jpg"
                            )

                        save_path = os.path.join(self.temp_dir, filename)

                        with open(save_path, "wb") as f:
                            f.write(body)

                        logger.info("[NXBST] Screenshot captured")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception as e:
                    logger.exception("[NXBST] Internal asset processing failed")
        except Exception as e:
            logger.exception("[NXBST] Network data stream analysis failed")

    async def process_viewer(self, page):
        try:
            logger.info("[NXBST] Preparing document viewing environment")
            consecutive_fails = 0
            previous_count = self.page_counter

            while True:
                await page.mouse.wheel(0, 1000)
                await page.keyboard.press("ArrowRight")
                await asyncio.sleep(6)

                if self.page_counter > previous_count:
                    consecutive_fails = 0
                    previous_count = self.page_counter
                else:
                    consecutive_fails += 1
                    logger.warning("[NXBST] No new pages detected, retrying")
                    await asyncio.sleep(2)

                if consecutive_fails > 6:
                    logger.info("[NXBST] Document scanning interrupted")
                    break
        except Exception as e:
            logger.exception("[NXBST] Document reading synchronization failed")

    async def compile_and_upload(self, title: str, author: str):
        import tempfile

        slug = urllib.parse.quote(title.lower().replace(" ", "-"), safe="")[:50]
        final_pdf_name = f"{slug}_{uuid7().hex[:6]}.pdf"

        temp_pdf_dir = tempfile.mkdtemp(prefix="nxbst_pdf_")
        pdf_path = os.path.join(temp_pdf_dir, final_pdf_name)

        files_by_page = {}
        for f in os.listdir(self.temp_dir):
            if f.startswith("nxbst_page_") and f.endswith(".jpg"):
                match = re.match(r"nxbst_page_(\d+)_tile(\d)\.jpg", f)
                if match:
                    page_num = match.group(1)
                    tile_num = match.group(2)
                    if page_num not in files_by_page:
                        files_by_page[page_num] = {}
                    files_by_page[page_num][tile_num] = os.path.join(self.temp_dir, f)
                elif "unknown" in f:
                    if "unknown" not in files_by_page:
                        files_by_page["unknown"] = []
                    files_by_page["unknown"].append(os.path.join(self.temp_dir, f))

        if not files_by_page:
            logger.warning("[NXBST] Skipping compilation due to no content")
            return

        images = []
        try:
            sorted_pages = sorted([p for p in files_by_page.keys() if p != "unknown"])
            logger.info("[NXBST] Synthesizing image segments")

            for p in sorted_pages:
                tiles_dict = files_by_page[p]
                try:
                    if "1" in tiles_dict:
                        t1 = Image.open(tiles_dict["1"]).convert("RGB")
                        width, height = t1.size
                        target_width = width * 2
                        target_height = height * 2
                        merged = Image.new("RGB", (target_width, target_height), (255, 255, 255))
                        merged.paste(t1, (0, 0))

                        if "2" in tiles_dict:
                            t2 = Image.open(tiles_dict["2"]).convert("RGB")
                            merged.paste(t2, (width, 0))
                        if "3" in tiles_dict:
                            t3 = Image.open(tiles_dict["3"]).convert("RGB")
                            merged.paste(t3, (0, height))
                        if "4" in tiles_dict:
                            t4 = Image.open(tiles_dict["4"]).convert("RGB")
                            merged.paste(t4, (width, height))

                        page_path = os.path.join(temp_pdf_dir, f"page_{p}.jpg")
                        merged.save(page_path, "JPEG")
                        images.append(page_path)
                    else:
                        for t in tiles_dict.values():
                            page_path = os.path.join(
                                temp_pdf_dir, f"page_single_{p}_{uuid7().hex[:6]}.jpg"
                            )
                            Image.open(t).convert("RGB").save(page_path, "JPEG")
                            images.append(page_path)
                except Exception as e:
                    logger.exception("[NXBST] Page image alignment failed")

            if "unknown" in files_by_page:
                for f in sorted(files_by_page["unknown"]):
                    try:
                        page_path = os.path.join(
                            temp_pdf_dir, f"page_unknown_{uuid7().hex[:6]}.jpg"
                        )
                        Image.open(f).convert("RGB").save(page_path, "JPEG")
                        images.append(page_path)
                    except Exception as e:
                        logger.exception("[NXBST] Image loading failed due to invalid format")

            if not images:
                raise RuntimeError("NXBST viewer returned no document pages")
            logger.info("[NXBST] Compiling images into PDF file")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(images))
            logger.info("[NXBST] Document compiled")

            logger.info("[NXBST] Transferring compiled document to permanent storage")
            minio_url = await storage.upload_local_file(
                f"system/collection/nxbst/{final_pdf_name}", pdf_path
            )

            if minio_url:
                metadata = await collected_metadata(
                    {
                        "title": title,
                        "author": author,
                        "source_url": self.source_url,
                        "collection_scope": self.collection_scope,
                    },
                    pdf_path,
                    minio_url,
                    "pdf",
                    "Nhà Xuất bản Chính trị quốc gia Sự thật",
                    "nxbst",
                )
                return await database.insert_document(metadata)

            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        except Exception:
            logger.exception("[NXBST] Document packaging and storage failed")
            raise
        finally:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            if os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)


class NxbstSource:
    @staticmethod
    async def probe_list_source() -> dict:
        url = "https://stbook.vn/cbs20/solr/search_from_app_mini.json?key=a"
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    payload = await response.json(content_type=None)
                    detected = len(payload.get("docs") or [])
                    reachable = response.status == 200 and detected > 0
                    return {
                        "source": "NXBST",
                        "reachable": reachable,
                        "http_status": response.status,
                        "documents_detected": detected,
                        "reason": None if reachable else "Source returned no document records",
                    }
        except Exception as error:
            return {
                "source": "NXBST",
                "reachable": False,
                "http_status": None,
                "documents_detected": 0,
                "reason": str(error)[:200],
            }

    @staticmethod
    async def run_list_collector(pages: int = 1, job_id: str | None = None):
        start_url = "https://stbook.vn/"
        logger.info("[NXBST] Scanning list from primary data source")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(start_url, timeout=60000)
                await asyncio.sleep(5)

                menu_css = "a.category-link"
                sub_cat_nodes = await page.query_selector_all(menu_css)

                category_urls = set()
                for node in sub_cat_nodes:
                    href = await node.get_attribute("href")
                    if href and ("/category/" in href or "/chuyen-muc/" in href):
                        category_urls.add(urllib.parse.urljoin(start_url, href))

                logger.info("[NXBST] Category analysis successful")

                documents_detected = 0
                documents_queued = 0
                pages_scanned = 0
                for cat_url in category_urls:
                    logger.info("[NXBST] Accessing subcategory for extraction")
                    await page.goto(cat_url, timeout=60000)
                    await asyncio.sleep(3)

                    current_page = 1
                    while True:
                        logger.info("[NXBST] Scanning category for document links")

                        document_nodes_css = (
                            '#main a[href*="store_detail"], #main a[href*="/sach/"]'
                        )
                        document_nodes = await page.query_selector_all(document_nodes_css)

                        found_documents = 0
                        for node in document_nodes:
                            href = await node.get_attribute("href")
                            if href:
                                full_url = urllib.parse.urljoin(start_url, href)
                                found_documents += 1
                                if not await dedup.is_collected("nxbst_url", full_url):
                                    published = await mq_client.publish(
                                        "collect_detail_queue",
                                        {
                                            "url": full_url,
                                            "source": "NXBST",
                                            "job_id": job_id,
                                            "collection_scope": {
                                                "type": "page",
                                                "value": current_page,
                                            },
                                        },
                                    )
                                    if not published:
                                        raise RuntimeError("RabbitMQ rejected an NXBST detail task")
                                    await dedup.mark_collected("nxbst_url", full_url)
                                    documents_queued += 1

                        documents_detected += found_documents
                        pages_scanned += 1

                        logger.info("[NXBST] Document added to queue")

                        if current_page >= pages:
                            logger.info("[NXBST] Reached collection page limit for category")
                            break

                        next_page_idx = current_page + 1
                        pagination_btn_xpath = f'xpath=//*[@id="pagination"]/nav/ul/li/a[text()="{next_page_idx}" or contains(text(), "»")]'

                        try:
                            next_btn = await page.query_selector(pagination_btn_xpath)
                            if next_btn:
                                await next_btn.click()
                                await asyncio.sleep(4)
                                current_page += 1
                            else:
                                break
                        except Exception:
                            break
                return {
                    "pages_scanned": pages_scanned,
                    "documents_detected": documents_detected,
                    "documents_queued": documents_queued,
                }
            except Exception as e:
                logger.exception("[NXBST] Page list scanning failed")
                raise

    @staticmethod
    async def run_detail_collector(
        document_url: str,
        job_id: str | None = None,
        collection_scope: dict | None = None,
    ):
        logger.info("[NXBST] Extracting document information")
        state_manager = State()

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            page.on("response", state_manager._handle_response)

            try:
                await page.goto(document_url, timeout=60000)
                await asyncio.sleep(4)

                title_el = await page.query_selector("#detail h1")
                raw_title = await title_el.inner_text() if title_el else document_url.split("/")[-1]
                safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title).strip()

                author_el = await page.query_selector("#detail .author a")
                raw_author = await author_el.inner_text() if author_el else "Unknown"

                logger.info("[NXBST] Data extracted, downloading")

                read_btn_css = '#whatchNow, a:has-text("Read Book"), a:has-text("View Now")'
                read_btn = await page.query_selector(read_btn_css)

                if read_btn:
                    logger.info("[NXBST] Preparing content collection environment")

                    import tempfile

                    state_manager.temp_dir = tempfile.mkdtemp(prefix=f"nxbst_{safe_title[:20]}_")
                    state_manager.source_url = document_url
                    state_manager.collection_scope = collection_scope

                    state_manager.captured_hashes = set()
                    state_manager.page_counter = 0

                    logger.info("[NXBST] Network filter initialized")
                    state_manager.is_capturing = True

                    await read_btn.click()
                    await asyncio.sleep(5)

                    await state_manager.process_viewer(page)

                    state_manager.is_capturing = False

                    document_id = await state_manager.compile_and_upload(raw_title, raw_author)
                    if not document_id:
                        raise RuntimeError("NXBST document was not persisted")
                    return document_id
                else:
                    raise RuntimeError("NXBST reader link was not found")
            except Exception as e:
                logger.exception("[NXBST] Document viewer synchronization failed")
                raise
