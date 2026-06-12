import asyncio
import os
import re
import hashlib
import urllib.parse
import shutil
from uuid6 import uuid7

import img2pdf
from playwright.async_api import async_playwright, Response
from loguru import logger

from src.core.db import db_client
from src.core.storage import storage
from src.core.redis_client import dedup
from src.core.browser import managed_browser, get_stealth_context

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
                        
                        logger.info(f"[Quy trình NXBGD] Chụp xong trang #{self.page_counter}: {filename}")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception as e:
                    logger.warning(f"Không bắt được dữ liệu trả về từ NXBGD: {e}")
        except Exception as e:
            logger.warning(f"Xử lý phản hồi từ NXBGD gặp sự cố: {e}")

    async def init_browser(self):
        self._browser_cm = managed_browser()
        self.browser = await self._browser_cm.__aenter__()
        self.context = await get_stealth_context(self.browser)
        self.page = await self.context.new_page()

    async def close(self):
        if self.context:
            await self.context.close()
        if hasattr(self, '_browser_cm'):
            await self._browser_cm.__aexit__(None, None, None)

    async def compile_and_upload(self, title: str):
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        final_pdf_name = f"{safe_title}_{uuid7().hex[:6]}.pdf"
        
        pdf_path = os.path.join(self.temp_dir, final_pdf_name)
        
        image_files = sorted([
            os.path.join(self.temp_dir, f) 
            for f in os.listdir(self.temp_dir) 
            if f.startswith("nxbgd_page_") and (f.endswith(".jpg") or f.endswith(".png"))
        ])

        if not image_files:
            logger.warning(f"Bỏ qua quyển PDF {title}: vì không lấy được trang nội dung nào")
            return

        try:
            logger.info(f"[NXBGD PDF] Đang gom {len(image_files)} trang thành '{final_pdf_name}' using img2pdf")
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(image_files))
            logger.info(f"[PDF NXBGD] Đã tạo PDF: {pdf_path}")
                
            logger.info(f"[Lưu trữ] Đang đẩy file {final_pdf_name} lên hệ thống lưu trữ")
            minio_url = await storage.upload_local_file(f"documents/nxbgd/{final_pdf_name}", pdf_path)
            
            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Extracted via NXBGD collector.",
                    "file_url": minio_url,
                    "tags": ["Nhà Xuất bản Giáo dục Việt Nam", "Unknown"],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "private",
                    "author_id": "nxbgd",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0
                }
                
                doc_id = await db_client.insert_document(document_metadata)
                if doc_id:
                    pass
                    
        except Exception as e:
            logger.error(f"[Lỗi hàng đợi thu thập NXBGD]: {e}")
            raise
        finally:

            logger.info(f"[Dọn dẹp NXBGD] Đang xóa thư mục tạm: {self.temp_dir}")
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Lỗi khi xóa thư mục tạm {self.temp_dir}: {e}")

    async def execute(self):
        await self.init_browser()
        
        url = f"https://taphuan.nxbgd.vn/tap-huan?grade={self.target_class}"
        try:
            logger.info(f"Đang truy cập URL gốc OLM: {url}")
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
                
                logger.info(f"Tìm thấy {len(document_urls)} tài liệu trên trang hiện tại cho tất cả các lớp")
                
                for doc_url in document_urls:
                    full_doc_url = f"https://taphuan.nxbgd.vn{doc_url}" if doc_url.startswith("/") else doc_url
                    logger.info(f"Đang xem thông tin tài liệu: {full_doc_url}")
                    
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
                                logger.info(f"Đang bỏ qua {full_title}, tài liệu đã tồn tại trong hàng đợi Redis")
                                continue
                                
                            await dedup.mark_collected("taphuan_book", full_title)
                            
                            viewer_url = await doc_link.get_attribute("href")
                            if viewer_url.startswith("/"): viewer_url = f"https://taphuan.nxbgd.vn{viewer_url}"
                            
                            logger.info(f"-> Processing Resource: {full_title} at {viewer_url}")
                            

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
                                    next_btn = await viewer_page.query_selector("button i.fa-angle-right")
                                    if next_btn:
                                        await next_btn.click()
                                    else:
                                        await viewer_page.keyboard.press("PageDown")
                                        await viewer_page.keyboard.press("Space")
                                except Exception as e:
                                    logger.warning(f"Lỗi điều hướng trong trình xem tài liệu: {e}")
                                await asyncio.sleep(2)  
                                
                                current_pages = len(self.captured_hashes)
                                if current_pages > 0 and current_pages == last_page_count:
                                    stable_count += 1
                                    if stable_count >= 4:
                                        logger.info(f"Đã thu thập {current_pages} trang, không phát hiện trang mới, hoàn tất tài liệu")
                                        break
                                else:
                                    stable_count = 0
                                last_page_count = current_pages
                            
                            self.is_capturing = False
                            await self.compile_and_upload(full_title)
                            await viewer_page.close()
                    except Exception as e:
                        logger.error(f"Kiểm tra chi tiết tài liệu gặp lỗi: {e}")
                        
                try:
                    await self.page.goto(url, timeout=60000)
                    await asyncio.sleep(5)
                    next_btn = await self.page.query_selector("button.p-paginator-next")
                    if next_btn and not await next_btn.is_disabled() and "p-disabled" not in (await next_btn.get_attribute("class") or ""):
                        logger.info(">>> Moving to Next Page >>>")
                        await next_btn.click()
                        await asyncio.sleep(4)
                    else:
                        has_next = False
                        logger.info("Reached end of pagination or next button not found")
                except Exception as e:
                    logger.error(f"Lỗi khi chuyển trang: {e}")
                    has_next = False
                    
                break

        except Exception as e:
            logger.error(f"Nguồn NXBGD báo lỗi: {e}")
            raise
        finally:
            await self.close()

async def run_nxbgd_collector(target_class: str):
    logger.info(f"Bắt đầu kéo dữ liệu từ NXBGD cho toàn bộ các lớp")
    collector = NXBGDCollector(target_class=target_class)
    await collector.execute()
