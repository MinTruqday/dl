import urllib.parse
import os
import aiohttp
import asyncio
import hashlib
from uuid6 import uuid7
from PIL import Image
import requests
import re
import shutil
import img2pdf
from playwright.async_api import async_playwright, Response
from playwright_stealth import stealth_async
from loguru import logger

from src.core.mq import mq_client
from src.core.redis_client import dedup
from src.core.storage import storage
from src.core.db import db_client
from src.core.browser import managed_browser, get_stealth_context

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
                            filename = f"nxbst_page_unknown_{self.page_counter:04d}_{uuid7().hex[:4]}.jpg"

                        save_path = os.path.join(self.temp_dir, filename)

                        with open(save_path, 'wb') as f:
                            f.write(body)

                        logger.info(f"Đã thu thập {filename}: {url[-50:]}")
                        self.captured_hashes.add(content_hash)
                        self.page_counter += 1
                except Exception as e:
                    logger.error(f"Lỗi vòng lặp bên trong: {e}")
        except Exception as e:
            logger.error(f"Lỗi vòng lặp bên ngoài: {e}")

    async def process_viewer(self, page):
        try:
            logger.info("Đang chuẩn bị vòng lặp để xử lý trang đọc tài liệu")
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
                    logger.warning(f"Chưa chụp được trang mới, thử lại lần {consecutive_fails}/6")
                    await asyncio.sleep(2)

                if consecutive_fails > 6:
                    logger.info("Đã quét toàn bộ tài liệu hoặc kết nối mạng bị gián đoạn")
                    break
        except Exception as e:
            logger.error(f"Lỗi trong lúc đọc tài liệu: {e}")

    async def compile_and_upload(self, title: str, author: str):
        import tempfile
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        final_pdf_name = f"{slug}_{uuid7().hex[:6]}.pdf"

        temp_pdf_dir = tempfile.mkdtemp(prefix="nxbst_pdf_")
        pdf_path = os.path.join(temp_pdf_dir, final_pdf_name)

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
            logger.warning(f"Bỏ qua quyển PDF {title}: vì không lấy được trang nội dung nào")
            return

        images = []
        try:
            sorted_pages = sorted([p for p in files_by_page.keys() if p != "unknown"])
            logger.info(f"Đang gom {len(sorted_pages)} trang bằng ma trận ghép \'final_pdf_name\'")

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

                        page_path = os.path.join(temp_pdf_dir, f"page_{p}.jpg")
                        merged.save(page_path, "JPEG")
                        images.append(page_path)
                    else:
                        for t in tiles_dict.values():
                            page_path = os.path.join(temp_pdf_dir, f"page_single_{p}_{uuid7().hex[:6]}.jpg")
                            Image.open(t).convert("RGB").save(page_path, "JPEG")
                            images.append(page_path)
                except Exception as e:
                    logger.warning(f"Lỗi ghép ảnh cho trang {p}: {e}")

            if "unknown" in files_by_page:
                for f in sorted(files_by_page["unknown"]):
                    try:
                        page_path = os.path.join(temp_pdf_dir, f"page_unknown_{uuid7().hex[:6]}.jpg")
                        Image.open(f).convert("RGB").save(page_path, "JPEG")
                        images.append(page_path)
                    except Exception as e:
                        logger.error(f"Lỗi tải các khối ảnh lạ: {e}")

            if images:
                logger.info("Đang dùng img2pdf để tạo file PDF")
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(images))
                logger.info(f"Đã tạo: {pdf_path}")

            logger.info(f"Đang đẩy file {final_pdf_name} lên hệ thống lưu trữ")
            minio_url = await storage.upload_local_file(f"tài liệu/nxbst/{final_pdf_name}", pdf_path)

            if minio_url:
                document_metadata = {
                    "title": title,
                    "slug": slug,
                    "description": "Đã trích xuất via NXBSTCollector Bot",
                    "file_url": minio_url,
                    "tags": ["Nhà Xuất bản Chính trị quốc gia Sự thật", author],
                    "content": None,
                    "content_format": "pdf",
                    "price": 0.0,
                    "visibility": "private",
                    "author_id": "nxbst",
                    "status": "published",
                    "views": 0,
                    "average_rating": 0.0
                }

                doc_id = await db_client.insert_document(document_metadata)

            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        except Exception as e:
            logger.error(f"Gặp lỗi: {e}")
        finally:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            if os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)

class NXBSTCollector:
    @staticmethod
    async def run_list_collector(pages: int = 0):
        start_url = "https://stbook.vn/"
        logger.info(f"Bắt đầu quét danh sách NXBST từ {start_url}")

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
                    if href and ('/category/' in href or '/chuyen-muc/' in href):
                        category_urls.add(urllib.parse.urljoin(start_url, href))

                logger.info(f"Lấy được {len(category_urls)} link danh mục (có cả Kho tài liệu)")

                for cat_url in category_urls:
                    logger.info(f"Đang vào danh mục: {cat_url}")
                    await page.goto(cat_url, timeout=60000)
                    await asyncio.sleep(3)

                    current_page = 1
                    while True:
                        logger.info(f"Đang lướt trang {current_page} của danh mục này")

                        document_nodes_css = '#main a[href*="store_detail"], #main a[href*="/sach/"]'
                        document_nodes = await page.query_selector_all(document_nodes_css)

                        found_documents = 0
                        for node in document_nodes:
                            href = await node.get_attribute("href")
                            if href:
                                full_url = urllib.parse.urljoin(start_url, href)
                                found_documents += 1
                                if not await dedup.is_collected("nxbst_url", full_url):
                                    await mq_client.publish("collect_detail_queue", {"url": full_url, "source": "NXBST"})
                                    await dedup.mark_collected("nxbst_url", full_url)

                        logger.info(f"Vừa đẩy {found_documents} tài liệu từ trang {current_page}")
                        
                        if current_page >= pages:
                            logger.info(f"Đã đủ số lượng {pages} trang cho danh mục này")
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
            except Exception as e:
                logger.error(f"Lỗi lúc vào xem chi tiết danh sách: {e}")
                raise

    @staticmethod
    async def run_detail_collector(document_url: str):
        logger.info(f"Đang xử lý chi tiết tài liệu NXBST: {document_url}")
        state_manager = NXBSTStreamState()

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            page.on("response", state_manager._handle_response)

            try:
                await page.goto(document_url, timeout=60000)
                await asyncio.sleep(4)

                title_el = await page.query_selector('#detail h1')
                raw_title = await title_el.inner_text() if title_el else document_url.split("/")[-1]
                safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title).strip()

                author_el = await page.query_selector('#detail .author a')
                raw_author = await author_el.inner_text() if author_el else "Unknown"

                logger.info(f"Đang tải quyển {raw_title} | Tác giả: {raw_author}")

                read_btn_css = '#whatchNow, a:has-text("Đọc sách"), a:has-text("Xem ngay")'
                read_btn = await page.query_selector(read_btn_css)

                if read_btn:
                    logger.info("Đã tìm thấy nút Đọc, chuẩn bị thu thập nội dung")

                    import tempfile
                    state_manager.temp_dir = tempfile.mkdtemp(prefix=f"nxbst_{safe_title[:20]}_")

                    state_manager.captured_hashes = set()
                    state_manager.page_counter = 0

                    logger.info("Đang thiết lập luồng theo dõi mạng ngầm")
                    state_manager.is_capturing = True

                    await read_btn.click()
                    await asyncio.sleep(5)

                    await state_manager.process_viewer(page)

                    state_manager.is_capturing = False

                    await state_manager.compile_and_upload(raw_title, raw_author)
                else:
                    logger.warning("Không tìm thấy nút Đọc hoặc Xem ngay trên trang")
            except Exception as e:
                logger.error(f"Gặp lỗi: {e}")
                raise
