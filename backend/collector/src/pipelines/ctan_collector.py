import urllib.parse
import os
import aiohttp
import random
import string
import zipfile
import requests
from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from loguru import logger

from src.core.mq import mq_client
from src.core.redis_client import dedup
from src.core.storage import storage
from src.core.db import db_client
from src.core.browser import managed_browser, get_stealth_context, download_file_with_retry

class CTANCollector:
    @staticmethod
    async def run_list_collector(pages: int = 0):
        logger.info(f"Bắt đầu thu thập danh sách bảng chữ cái CTAN")
        
        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                for letter in string.ascii_uppercase:
                    search_url = f"https://www.ctan.org/pkg/:{letter}"
                    logger.info(f"Đang duyệt danh mục CTAN: {letter} -> {search_url}")
                    
                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    list_css = 'main a[href*="/pkg/"]'
                    
                    try:
                        await page.wait_for_selector('main', timeout=15000)
                    except Exception as e:
                        logger.warning(f"Hết giờ hoặc không có dữ liệu cho ký tự {letter}: {e}")
                        continue
                    
                    book_nodes = await page.query_selector_all(list_css)
                    book_urls = set()
                    
                    for node in book_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = "https://www.ctan.org" + href if href.startswith("/") else href
                            book_urls.add(full_url)
                    
                    logger.info(f"Gom được {len(book_urls)} gói cho ký tự {letter}")
                    for url in book_urls:
                        if not await dedup.is_collected("ctan_url", url):
                            await mq_client.publish("collect_detail_queue", {"url": url, "source": "CTAN"})
                            await dedup.mark_collected("ctan_url", url)
                            
            except Exception as e:
                logger.error(f"[Quét danh sách CTAN bị lỗi]: {e}")
                raise

    @staticmethod
    async def run_detail_collector(book_url: str):
        logger.info(f"[Tải dữ liệu] CTAN: {book_url}")
        
        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                await page.goto(book_url, timeout=60000)
                await page.wait_for_timeout(2000)
                
                payload = {}
                payload["source_url"] = book_url
                
                title_el = await page.query_selector('main h1')
                raw_title = await title_el.inner_text() if title_el else book_url.split("/")[-1]
                payload["title"] = raw_title.strip()
                
                desc_el = await page.query_selector('main p')
                payload["description"] = await desc_el.inner_text() if desc_el else "No description available."
                
                author_el = await page.query_selector('main table td a[href*="/author/"]')
                authors_list = []
                if author_el:
                    raw_authors = await author_el.inner_text()
                    split_authors = re.split(r'\n|,', raw_authors)
                    authors_list = [a.strip() for a in split_authors if a.strip()]
                payload["authors"] = authors_list if authors_list else ["Unknown Author"]
                
                download_el = await page.query_selector('main a[href$=".zip"], main a:has-text("Download")')
                
                if download_el:
                    download_link = await download_el.get_attribute("href")
                    if download_link:
                        full_download_url = "https://www.ctan.org" + download_link if download_link.startswith("/") else download_link
                        payload["download_link"] = full_download_url
                        
                        logger.info(f"Đã lấy được link tải: {full_download_url}")
                        
                        slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"))[:50]
                        payload["filename"] = f"{slug}.zip"
                        payload["content_format"] = "zip"
                        
                        await mq_client.publish("download_processor_queue", {**payload, "source": "CTAN"})
                    else:
                        logger.warning(f"Link tải bị trống trên trang: {book_url}")
                else:
                    logger.warning(f"Tìm mỏi mắt không thấy nút tải ở XPath trên trang: {book_url}")
                
            except Exception as e:
                logger.error(f"[Lỗi thu thập chi tiết CTAN]: {e}")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        import tempfile
        import shutil
        
        url = payload.get("download_link")
        title = payload.get("title", "package")
        
        if not url:
            logger.error(f"[Tải dữ liệu] URL tải trọng không hợp lệ: {title}")
            return
            
        logger.info(f"[Tải dữ liệu] Đang tiến hành tải file thực tế và giải nén: {title}")
        
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        filename = payload.get("filename") or f"{slug}.zip"
        
        temp_base = tempfile.mkdtemp(prefix="ctan_")
        target_zip_local = os.path.join(temp_base, filename)
        extracted_folder_path = os.path.join(temp_base, "extracted", slug)
        
        minio_url_book = None
        
        try:
            success = await download_file_with_retry(url, target_zip_local)
            if success:
                logger.info(f"[Quy trình CTAN] Đã tải về bộ nhớ tạm: {target_zip_local}")
                
                minio_url_book = await storage.upload_local_file(f"books/ctan/{filename}", target_zip_local)
                        
                logger.info(f"Đang xả nén file ZIP")
                os.makedirs(extracted_folder_path, exist_ok=True)
                with zipfile.ZipFile(target_zip_local, 'r') as zip_ref:
                    zip_ref.extractall(extracted_folder_path)
                    
                search_root = extracted_folder_path
                contents = os.listdir(extracted_folder_path)
                if len(contents) == 1 and os.path.isdir(os.path.join(extracted_folder_path, contents[0])):
                    search_root = os.path.join(extracted_folder_path, contents[0])
                    logger.info(f"Có thư mục lồng nhau: {contents[0]}, hệ thống đang tự động căn chỉnh lại")

                found_pdf = None
                for root, _, files in os.walk(search_root):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            if slug in f.lower() or "doc" in root.lower():
                                found_pdf = os.path.join(root, f)
                                break
                    if found_pdf: break
                
                if found_pdf:
                    pdf_filename = os.path.basename(found_pdf)
                    minio_url_pdf = await storage.upload_local_file(f"documents/ctan/{pdf_filename}", found_pdf)
                    logger.info(f"Đã lấy và tải file PDF chính lên: {minio_url_pdf}")
                    payload["pdf_url"] = minio_url_pdf
                    
                md_content = f"# Source code for {title}\n\n"
                allowed_exts = {".tex", ".sty", ".cls", ".dtx", ".ins", ".bib", ".def", ".pl", ".txt"}
                for root_dir, _, files in os.walk(search_root):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in allowed_exts:
                            file_path = os.path.join(root_dir, f)
                            rel_path = os.path.relpath(file_path, search_root)
                            try:
                                with open(file_path, "r", encoding="utf-8") as text_file:
                                    content = text_file.read()
                                    md_content += f"## File: {rel_path}\n```latex\n{content}\n```\n\n"
                            except UnicodeDecodeError:
                                pass
                            except Exception as e:
                                logger.warning(f"Đọc file thất bại {rel_path}: {e}")
                                
                md_filename = f"{slug}_source.md"
                md_path = os.path.join(temp_base, md_filename)
                with open(md_path, "w", encoding="utf-8") as md_f:
                    md_f.write(md_content)
                    
                minio_url_md = await storage.upload_local_file(f"documents/ctan/{md_filename}", md_path)
                logger.info(f"Đã đóng gói và đẩy file Markdown lên: {minio_url_md}")
                payload["markdown_url"] = minio_url_md
                
                logger.info(f"Xử lý êm xuôi {filename}")
            else:
                logger.error(f"[Lỗi tải xuống CTAN] Tải thất bại {url}")
                return
        except Exception as e:
            logger.error(f"[Lỗi mạng hoặc lúc trích xuất]: {e}")
            raise
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)
            
        if minio_url_book:
            logger.info(f"[Thành công] Đã lưu bộ dữ liệu lên hệ thống lưu trữ: {minio_url_book}")
            
            book_document = {
                "title": title,
                "slug": slug,
                "description": payload.get("description", "Extracted via CTAN bot."),
                "file_url": minio_url_book,
                "pdf_url": payload.get("pdf_url"),
                "markdown_url": payload.get("markdown_url"),
                "tags": ["CTAN"] + (payload.get("authors") if payload.get("authors") else ["Unknown"]),
                "content_format": "zip",
                "price": 0.0,
                "visibility": "private",
                "author_id": "ctan",
                "status": "published",
                "rag_status": "pending",
                "views": 0,
                "average_rating": 0.0
            }
            
            doc_id = await db_client.insert_document(book_document)