import asyncio
import hashlib
import os
import re
import shutil
import tempfile
import urllib.parse
import img2pdf
from loguru import logger
from PIL import Image
from playwright.async_api import Response
from playwright_stealth import stealth_async
from core.config import settings
from src.core.browser import get_stealth_context, managed_browser
from src.core.db import db_client
from src.core.mq import mq_client
from src.core.redis import dedup
from src.core.storage import storage
from uuid6 import uuid7

MIN_FILE_SIZE_BYTES = settings.MIN_FILE_SIZE_BYTES

class NXBSTStreamState:
    def __init__(self):
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

            if "image" in content_type or "img.json" in url or any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                if any(skip in url for skip in ["icon", "avatar", "logo", "button", "bg", "banner", "preview.png"]):
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
                            filename = f"nxbst_page_unknown_{self.page_counter:04d}_{uuid7().hex[:4]}.jpg"

                        save_path = os.path.join(self.temp_dir, filename)

                        with open(save_path, "wb") as f:
                            f.write(body)

                        logger.info("Visual capture module successfully intercepted and collected high resolution structural page asset")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception:
                    logger.error("Internal asset processing loop encountered unexpected failure reading functional network response payload body")
        except Exception:
            logger.error("External network interception loop encountered unexpected structural issue analyzing incoming active response stream")

    async def process_viewer(self, page):
        try:
            logger.info("Collection module actively preparing functional document viewer environment for automated systematic reading sequence")
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
                    logger.warning("Visual capture module detected no new pages and is preparing automated functional retry sequence")
                    await asyncio.sleep(2)

                if consecutive_fails > 6:
                    logger.info("Automated systematic document scanning sequence concluded or secure network connection safely interrupted gracefully")
                    break
        except Exception:
            logger.error("Automated structural document reading sequence failed due to unexpected dynamic interaction synchronization issue")

    async def compile_and_upload(self, title: str, author: str):
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
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
            logger.warning("Document compilation structural process automatically skipped because no readable content blocks were detected")
            return

        images = []
        try:
            sorted_pages = sorted([p for p in files_by_page.keys() if p != "unknown"])
            logger.info("Rendering engine actively synthesizing collected image fragments into structured chronological dimensional matrix")

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
                            merged.paste(Image.open(tiles_dict["2"]).convert("RGB"), (width, 0))
                        if "3" in tiles_dict:
                            merged.paste(Image.open(tiles_dict["3"]).convert("RGB"), (0, height))
                        if "4" in tiles_dict:
                            merged.paste(Image.open(tiles_dict["4"]).convert("RGB"), (width, height))

                        page_path = os.path.join(temp_pdf_dir, f"page_{p}.jpg")
                        merged.save(page_path, "JPEG")
                        images.append(page_path)
                    else:
                        for t in tiles_dict.values():
                            page_path = os.path.join(temp_pdf_dir, f"page_single_{p}_{uuid7().hex[:6]}.jpg")
                            Image.open(t).convert("RGB").save(page_path, "JPEG")
                            images.append(page_path)
                except Exception:
                    logger.warning("Image structural stitching algorithm encountered spatial alignment error processing specific document page matrix")

            if "unknown" in files_by_page:
                for f in sorted(files_by_page["unknown"]):
                    try:
                        page_path = os.path.join(temp_pdf_dir, f"page_unknown_{uuid7().hex[:6]}.jpg")
                        Image.open(f).convert("RGB").save(page_path, "JPEG")
                        images.append(page_path)
                    except Exception:
                        logger.error("Image processing rendering engine failed loading irregular visual block due to format metadata corruption")

            if images:
                logger.info("Rendering engine actively compiling sorted image sequence into unified portable structural document format")
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(images))
                logger.info("Unified functional document successfully compiled and verified by primary rendering engine matrix")

            logger.info("Compiled structural document securely transferring to permanent distributed object storage operational backend")
            minio_url = await storage.upload_local_file(f"documents/nxbst/{final_pdf_name}", pdf_path)

            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Extracted via automated collection process",
                    "file_url": minio_url,
                    "tags": ["Nhà Xuất bản Chính trị quốc gia Sự thật", author],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "private",
                    "creator_id": "nxbst",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0,
                }
                await db_client.insert_document(document_metadata)

            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        except Exception:
            logger.error("Unexpected structural system failure occurred during final dimensional document assembly and storage sequence")
        finally:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            if os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)

class NXBSTPipeline:
    @staticmethod
    async def collect_list(pages: int = 0):
        start_url = "https://stbook.vn/"
        logger.info("System initializing comprehensive categorical structural list scan from designated primary data source host")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(start_url, timeout=60000)
                await asyncio.sleep(5)

                menu_css = '.left-menu-item a[href]:not([href*="javascript"])'
                sub_cat_nodes = await page.query_selector_all(menu_css)

                category_urls = set()
                for node in sub_cat_nodes:
                    href = await node.get_attribute("href")
                    if href and ("/category/" in href or "/chuyen-muc/" in href):
                        category_urls.add(urllib.parse.urljoin(start_url, href))

                logger.info("Categorical indexing operational process successfully identified all available subcategory dynamic navigational reference links")

                for cat_url in category_urls:
                    logger.info("Automated collection bot navigating specific subcategory structural view initiating extraction phase matrix")
                    await page.goto(cat_url, timeout=60000)
                    await asyncio.sleep(3)

                    current_page = 1
                    while True:
                        logger.info("Collection bot systematically scanning current categorical dynamic page finding nested functional document references")

                        document_nodes_css = '#main a[href*="store_detail"], #main a[href*="/sach/"]'
                        document_nodes = await page.query_selector_all(document_nodes_css)

                        for node in document_nodes:
                            href = await node.get_attribute("href")
                            if href:
                                full_url = urllib.parse.urljoin(start_url, href)
                                if not await dedup.is_collected("nxbst_url", full_url):
                                    await mq_client.publish("collect_detail_queue", {"url": full_url, "source": "NXBST"})
                                    await dedup.mark_collected("nxbst_url", full_url)

                        logger.info("Newly discovered structural functional document references securely added internal processing operational queue")

                        if current_page >= pages:
                            logger.info("Collection operational process successfully reached maximum designated numerical page boundary active category")
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
            except Exception:
                logger.error("Systematic structural list scanning process encountered critical failure retrieving required functional navigational details")
                raise

    @staticmethod
    async def collect_detail(document_url: str):
        logger.info("Collection bot currently extracting comprehensive functional metadata structural profile targeted specific document")
        state_manager = NXBSTStreamState()

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

                logger.info("Extraction sequence successfully identified primary structural document metadata proceeding active download phase")

                read_btn_css = '#whatchNow, a:has-text("Read Book"), a:has-text("View Now")'
                read_btn = await page.query_selector(read_btn_css)

                if read_btn:
                    logger.info("Valid reading access mechanism detected system preparing functional environment active structural content collection")

                    state_manager.temp_dir = tempfile.mkdtemp(prefix=f"nxbst_{safe_title[:20]}_")
                    state_manager.captured_hashes = set()
                    state_manager.page_counter = 0

                    logger.info("Network interception structural module successfully initialized actively monitoring dynamic incoming spatial data stream")
                    state_manager.is_capturing = True

                    await read_btn.click()
                    await asyncio.sleep(5)

                    await state_manager.process_viewer(page)

                    state_manager.is_capturing = False
                    await state_manager.compile_and_upload(raw_title, raw_author)
                else:
                    logger.warning("Required reading operational access mechanism undefined within active functional document structural viewer rendering")
            except Exception:
                logger.error("Unexpected structural synchronization rendering error attempting intercept dynamic document active viewing stream")
                raise