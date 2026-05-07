import urllib.parse
import os
import aiohttp
import random
import asyncio
import hashlib
from uuid import uuid4
from PIL import Image
import requests
from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright, Response
from playwright_stealth import stealth_async
from loguru import logger
import shutil
from src.core.mq import mq_client
from src.core.redis_client import dedup
from src.core.storage import storage
from src.core.db import db_client
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
]
MIN_FILE_SIZE_BYTES = 5000
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
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type or 'img.json' in url or any(ext in url for ext in ['.jpg', '.jpeg', '.png']):
                if any(skip in url for skip in ['icon', 'avatar', 'logo', 'button', 'bg', 'banner', 'preview.png']):
                    return
                try:
                    body = await response.body()
                    if len(body) > MIN_FILE_SIZE_BYTES:
                        content_hash = hashlib.md5(body).hexdigest()
                        if content_hash in self.captured_hashes:
                            return
                        match = re.search(r'img_short_(\d+)(\d)', url)
                        if match:
                            page_num = int(match.group(1))
                            tile_num = int(match.group(2))
                            filename = f"nxbst_page_{page_num:04d}_tile{tile_num}.jpg"
                        else:
                            filename = f"nxbst_page_unknown_{self.page_counter:04d}_{uuid4().hex[:4]}.jpg"
                        save_path = os.path.join(self.temp_dir, filename)
                        with open(save_path, 'wb') as f:
                            f.write(body)
                        logger.info(f"[NXBSTStream] Captured {filename}: {url[-50:]}")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception as e:
                    logger.error(f"[NXBSTStreamState] Inner exception: {e}")
        except Exception as e:
            logger.error(f"[NXBSTStreamState] Outer exception: {e}")
    async def process_viewer(self, page):
        try:
            logger.info("Initializing viewer processing loop")
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
                    logger.warning(f"No new pages captured, retry {consecutive_fails}/6")
                    await asyncio.sleep(2)
                if consecutive_fails > 6:
                    logger.info("End of document detected or network Stream stopped.")
                    break
        except Exception as e:
            logger.error(f"Viewer loop error: {e}")
    async def compile_and_upload(self, title: str, author: str):
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        final_pdf_name = f"{slug}_{uuid4().hex[:6]}.pdf"
        os.makedirs("/app/documents/nxbst", exist_ok=True)
        pdf_path = f"/app/documents/nxbst/{final_pdf_name}"
        files_by_page = {}
        for f in os.listdir(self.temp_dir):
            if f.startswith("nxbst_page_") and f.endswith(".jpg"):
                match = re.match(r'nxbst_page_(\d+)_tile(\d)\.jpg', f)
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
            logger.warning(f"Skipping PDF {title}: No pages collected.")
            return
        images = []
        try:
            sorted_pages = sorted([p for p in files_by_page.keys() if p != "unknown"])
            logger.info(f"[NXBSTPDF] Compiling {len(sorted_pages)} pages with tile matrix 1/2/3/4 '{final_pdf_name}'")
            for p in sorted_pages:
                tiles_dict = files_by_page[p]
                try:
                    if '1' in tiles_dict:
                        t1 = Image.open(tiles_dict['1']).convert("RGB")
                        width, height = t1.size
                        target_width = width * 2
                        target_height = height * 2
                        merged = Image.new("RGB", (target_width, target_height), (255, 255, 255))
                        merged.paste(t1, (0, 0))
                        if '2' in tiles_dict:
                            t2 = Image.open(tiles_dict['2']).convert("RGB")
                            merged.paste(t2, (width, 0))
                        if '3' in tiles_dict:
                            t3 = Image.open(tiles_dict['3']).convert("RGB")
                            merged.paste(t3, (0, height))
                        if '4' in tiles_dict:
                            t4 = Image.open(tiles_dict['4']).convert("RGB")
                            merged.paste(t4, (width, height))
                        images.append(merged)
                    else:
                        for t in tiles_dict.values():
                            images.append(Image.open(t).convert("RGB"))
                except Exception as e:
                    logger.warning(f"Failed to merge tiles for page {p}: {e}")
            if "unknown" in files_by_page:
                for f in sorted(files_by_page["unknown"]):
                    try:
                        images.append(Image.open(f).convert("RGB"))
                    except Exception as e:
                        logger.error(f"Failed to load unknown tile: {e}")
            if images:
                images[0].save(pdf_path, save_all=True, append_images=images[1:])
                logger.info(f"[NXBSTPDF SUCCESS] Created: {pdf_path}")
            logger.info(f"[NXBSTStorage] Uploading {final_pdf_name} to MinIO")
            minio_url = await storage.upload_local_file(f"documents/nxbst/{final_pdf_name}", pdf_path)
            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Extracted via NXBSTCollector Bot.",
                    "file_url": minio_url,
                    "tags": ["Nhà Xuất bản Chính trị quốc gia Sự thật", author],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "public",
                    "author_id": "nxbst_collector",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0
                }
                doc_id = await db_client.insert_document(document_metadata)
                if doc_id:
                    await mq_client.publish("format_converter_queue", {"document_id": doc_id, "file_url": minio_url, "filename": final_pdf_name})
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            logger.error(f"[NXBSTPDF Compile Error]: {e}")
        finally:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
class NXBSTCollector:
    @staticmethod
    async def run_list_collector():
        start_url = "https://stbook.vn/"
        logger.info(f"Starting List Collection on NXBST {start_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--js-flags=--max-old-space-size=4096'
                ]
            )
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            await stealth_async(page)
            try:
                await page.goto(start_url, timeout=60000)
                await asyncio.sleep(5)
                menu_xpath = 'xpath=//div[contains(@class, "left-menu-item")]//a[@href and not(contains(@href, "javascript"))]'
                sub_cat_nodes = await page.query_selector_all(menu_xpath)
                category_urls = set()
                for node in sub_cat_nodes:
                    href = await node.get_attribute("href")
                    if href and ('/category/' in href or '/chuyen-muc/' in href):
                        category_urls.add(urllib.parse.urljoin(start_url, href))
                logger.info(f"Successfully extracted {len(category_urls)} category URLs including Kho tài liệu")
                for cat_url in category_urls:
                    logger.info(f"Scanning Category: {cat_url}")
                    await page.goto(cat_url, timeout=60000)
                    await asyncio.sleep(3)
                    current_page = 1
                    while True:
                        logger.info(f"Scanning Page {current_page} of current category")
                        document_nodes_xpath = 'xpath=//*[@id="main"]//a[contains(@href, "store_detail") or contains(@href, "/sach/")]'
                        document_nodes = await page.query_selector_all(document_nodes_xpath)
                        found_documents = 0
                        for node in document_nodes:
                            href = await node.get_attribute("href")
                            if href:
                                full_url = urllib.parse.urljoin(start_url, href)
                                found_documents += 1
                                if not await dedup.is_collected("nxbst_url", full_url):
                                    await mq_client.publish("collect_detail_queue", {"url": full_url, "source": "NXBST"})
                                    await dedup.mark_collected("nxbst_url", full_url)
                        logger.info(f"Pushed {found_documents} documents to MQ from page {current_page}.")
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
            except Exception as e:
                logger.error(f"[NXBSTList Collector Error]: {e}")
            finally:
                await browser.close()
    @staticmethod
    async def run_detail_collector(document_url: str):
        logger.info(f"[Detail Collector] NXBST {document_url}")
        state_manager = NXBSTStreamState()
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--js-flags=--max-old-space-size=4096'
                ]
            )
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            await stealth_async(page)
            page.on("response", state_manager._handle_response)
            try:
                await page.goto(document_url, timeout=60000)
                await asyncio.sleep(4)
                title_xpath = 'xpath=//*[@id="detail"]/div[2]/div/h1'
                title_el = await page.query_selector(title_xpath)
                raw_title = await title_el.inner_text() if title_el else document_url.split("/")[-1]
                safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title).strip()
                author_xpath = 'xpath=//*[@id="detail"]/div[2]/div/div[1]/a'
                author_el = await page.query_selector(author_xpath)
                raw_author = await author_el.inner_text() if author_el else "Unknown Author"
                logger.info(f"Targeting document {raw_title} | Author: {raw_author}")
                read_btn_xpath = 'xpath=//*[@id="whatchNow"]'
                read_btn = await page.query_selector(read_btn_xpath)
                if read_btn:
                    logger.info("Found watch/read button. Preparing to capture")
                    os.makedirs("/app/documents/nxbst_temp", exist_ok=True)
                    state_manager.temp_dir = f"/app/documents/nxbst_temp/{safe_title}"
                    os.makedirs(state_manager.temp_dir, exist_ok=True)
                    state_manager.captured_hashes = set()
                    state_manager.page_counter = 0
                    logger.info("Initializing background network Stream capture")
                    state_manager.is_capturing = True
                    await read_btn.click()
                    await asyncio.sleep(5)
                    await state_manager.process_viewer(page)
                    state_manager.is_capturing = False
                    await state_manager.compile_and_upload(raw_title, raw_author)
                else:
                    logger.warning("Read/Watch Now button not found.")
            except Exception as e:
                logger.error(f"[NXBSTDetail Collector Error]: {e}")
            finally:
                await browser.close()
