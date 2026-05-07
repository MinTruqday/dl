import asyncio
import os
import re
import hashlib
import time
import urllib.parse
import shutil
from uuid import uuid4
from PIL import Image
from playwright.async_api import async_playwright, Response
from loguru import logger
from src.core.db import db_client
from src.core.storage import storage
from src.core.mq import mq_client
from src.core.redis_client import dedup
MIN_FILE_SIZE_BYTES = 20000
class NXBGDCollector:
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
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type or any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png']):
                if any(skip in url for skip in ['icon', 'avatar', 'logo', 'button', 'blank_book_page']):
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
                        with open(save_path, 'wb') as f:
                            f.write(body)
                        logger.info(f"[NXBGD Stream] Captured page
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception as e:
logger.info("Log message sanitized"))
        except Exception as e:
logger.info("Log message sanitized"))
    async def init_browser(self):
        self.p = await async_playwright().start()
        self.browser = await self.p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-application-cache',
                '--mute-audio',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--js-flags=--max-old-space-size=4096'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()
    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.p:
            await self.p.stop()
    async def compile_and_upload(self, title: str):
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        final_pdf_name = f"{safe_title}_{uuid4().hex[:6]}.pdf"
        pdf_path = os.path.join(self.temp_dir, final_pdf_name)
        image_files = sorted([
            os.path.join(self.temp_dir, f) 
            for f in os.listdir(self.temp_dir) 
            if f.startswith("nxbgd_page_") and (f.endswith(".jpg") or f.endswith(".png"))
        ])
        if not image_files:
logger.info("Log message sanitized"))
            return
        try:
logger.info("Log message sanitized"))
            images = []
            for f in image_files:
                try:
                    img = Image.open(f).convert("RGB")
                    images.append(img)
                except Exception as e:
logger.info("Log message sanitized"))
            if images:
                images[0].save(pdf_path, save_all=True, append_images=images[1:])
logger.info("Log message sanitized"))
logger.info("Log message sanitized"))
            minio_url = await storage.upload_local_file(f"documents/nxbgd/{final_pdf_name}", pdf_path)
            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Extracted via NXBGD collector (OLM API).",
                    "file_url": minio_url,
                    "tags": ["NXB Giao duc"],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "public",
                    "author_id": "nxbgd-collector",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0
                }
                doc_id = await db_client.insert_document(document_metadata)
                if doc_id:
                    await mq_client.publish("format_converter_queue", {"document_id": doc_id, "file_url": minio_url, "filename": final_pdf_name})
        except Exception as e:
logger.info("Log message sanitized"))
        finally:
logger.info("Log message sanitized"))
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
logger.info("Log message sanitized"))
    async def execute(self):
        await self.init_browser()
        url = f"https://taphuan.nxbgd.vn/tap-huan?grade=-1"
        try:
logger.info("Log message sanitized"))
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
logger.info("Log message sanitized"))
                for doc_url in document_urls:
                    full_doc_url = f"https://taphuan.nxbgd.vn{doc_url}" if doc_url.startswith("/") else doc_url
logger.info("Log message sanitized"))
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
logger.info("Log message sanitized"))
                                continue
                            await dedup.mark_collected("taphuan_book", full_title)
                            viewer_url = await doc_link.get_attribute("href")
                            if viewer_url.startswith("/"): viewer_url = f"https://taphuan.nxbgd.vn{viewer_url}"
logger.info("Log message sanitized"))
                            self.temp_dir = f"/app/documents/nxbgd/temp/{safe_title}"
                            os.makedirs(self.temp_dir, exist_ok=True)
                            self.captured_hashes = set()
                            self.page_counter = 0
                            self.is_capturing = True
                            viewer_page = await self.context.new_page()
                            viewer_page.on("response", self._handle_response)
                            await viewer_page.goto(viewer_url, timeout=60000)
                            await asyncio.sleep(5)
                            for _ in range(40):
                                try:
                                    next_btn = await viewer_page.query_selector("button i.fa-angle-right")
                                    if next_btn:
                                        await next_btn.click()
                                    else:
                                        await viewer_page.keyboard.press("PageDown")
                                        await viewer_page.keyboard.press("Space")
                                except Exception as e:
logger.info("Log message sanitized"))
                                await asyncio.sleep(2) 
                            self.is_capturing = False
                            await self.compile_and_upload(full_title)
                            await viewer_page.close()
                    except Exception as e:
logger.info("Log message sanitized"))
                try:
                    await self.page.goto(url, timeout=60000)
                    await asyncio.sleep(5)
                    next_btn = await self.page.query_selector("button.p-paginator-next")
                    if next_btn and not await next_btn.is_disabled() and "p-disabled" not in (await next_btn.get_attribute("class") or ""):
logger.info("Log message sanitized"))
                        await next_btn.click()
                        await asyncio.sleep(4)
                    else:
                        has_next = False
logger.info("Log message sanitized"))
                except Exception as e:
logger.info("Log message sanitized"))
                    has_next = False
                break
        except Exception as e:
logger.info("Log message sanitized"))
        finally:
            await self.close()
async def run_nxbgd_collector(target_class: str):
logger.info("Log message sanitized"))
    collector = NXBGDCollector(target_class=target_class)
    await collector.execute()
