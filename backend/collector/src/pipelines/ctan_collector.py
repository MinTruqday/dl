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
from src.core.browser import get_playwright_browser, get_stealth_context, download_file_with_retry

class CTANCollector:
    @staticmethod
    async def run_list_collector(pages: int = 0):
        logger.info(f"Starting CTAN Alphabetical List Collector")
        
        async with async_playwright() as p:
            browser = await get_playwright_browser(p)
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                for letter in string.ascii_uppercase:
                    search_url = f"https://www.ctan.org/pkg/:{letter}"
                    logger.info(f"Scanning CTAN Category: {letter} -> {search_url}")
                    
                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    list_css = 'main a[href*="/pkg/"]'
                    
                    try:
                        await page.wait_for_selector('main', timeout=15000)
                    except Exception as e:
                        logger.warning(f"Timeout or empty container for letter {letter}: {e}")
                        continue
                    
                    book_nodes = await page.query_selector_all(list_css)
                    book_urls = set()
                    
                    for node in book_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = "https://www.ctan.org" + href if href.startswith("/") else href
                            book_urls.add(full_url)
                    
                    logger.info(f"Found {len(book_urls)} packages for letter {letter}")
                    for url in book_urls:
                        if not await dedup.is_collected("ctan_url", url):
                            await mq_client.publish("collect_detail_queue", {"url": url, "source": "CTAN"})
                            await dedup.mark_collected("ctan_url", url)
                            
            except Exception as e:
                logger.error(f"[CTAN List Collector Error]: {e}")
                raise
            finally:
                await browser.close()

    @staticmethod
    async def run_detail_collector(book_url: str):
        logger.info(f"[Detail Collector] CTAN: {book_url}")
        
        async with async_playwright() as p:
            browser = await get_playwright_browser(p)
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
                        
                        logger.info(f"Successfully extracted completed download link: {full_download_url}")
                        
                        slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"))[:50]
                        payload["filename"] = f"{slug}.zip"
                        payload["content_format"] = "zip"
                        
                        await mq_client.publish("download_processor_queue", {**payload, "source": "CTAN"})
                    else:
                        logger.warning(f"Download link attribute empty on detail page: {book_url}")
                else:
                    logger.warning(f"Download button not found at specified XPath on detail page: {book_url}")
                
            except Exception as e:
                logger.error(f"[CTAN Detail Collector Error]: {e}")
                raise
            finally:
                await browser.close()

    @staticmethod
    async def run_download_processor(payload: dict):
        import tempfile
        import shutil
        
        url = payload.get("download_link")
        title = payload.get("title", "package")
        
        if not url:
            logger.error(f"[Download Processor] Invalid payload URL: {title}")
            return
            
        logger.info(f"[Download Processor] Processing physical download and extraction: {title}")
        
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        filename = payload.get("filename") or f"{slug}.zip"
        
        temp_base = tempfile.mkdtemp(prefix="ctan_")
        target_zip_local = os.path.join(temp_base, filename)
        extracted_folder_path = os.path.join(temp_base, "extracted", slug)
        
        minio_url_book = None
        
        try:
            success = await download_file_with_retry(url, target_zip_local)
            if success:
                logger.info(f"[CTAN Stream] Downloaded to temp: {target_zip_local}")
                
                minio_url_book = await storage.upload_local_file(f"books/ctan/{filename}", target_zip_local)
                        
                logger.info(f"Extracting ZIP archive")
                os.makedirs(extracted_folder_path, exist_ok=True)
                with zipfile.ZipFile(target_zip_local, 'r') as zip_ref:
                    zip_ref.extractall(extracted_folder_path)
                    
                search_root = extracted_folder_path
                contents = os.listdir(extracted_folder_path)
                if len(contents) == 1 and os.path.isdir(os.path.join(extracted_folder_path, contents[0])):
                    search_root = os.path.join(extracted_folder_path, contents[0])
                    logger.info(f"Detected nested folder: {contents[0]}, adjusting search root.")

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
                    logger.info(f"Found and uploaded primary PDF: {minio_url_pdf}")
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
                                logger.warning(f"Failed to read {rel_path}: {e}")
                                
                md_filename = f"{slug}_source.md"
                md_path = os.path.join(temp_base, md_filename)
                with open(md_path, "w", encoding="utf-8") as md_f:
                    md_f.write(md_content)
                    
                minio_url_md = await storage.upload_local_file(f"documents/ctan/{md_filename}", md_path)
                logger.info(f"Compiled and uploaded Markdown source: {minio_url_md}")
                payload["markdown_url"] = minio_url_md
                
                logger.info(f"Successfully processed {filename}.")
            else:
                logger.error(f"[CTAN Download Error] Failed to download {url}")
                return
        except Exception as e:
            logger.error(f"[Aiohttp/Extraction Error]: {e}")
            raise
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)
            
        if minio_url_book:
            logger.info(f"[Success] Package saved to MinIO: {minio_url_book}")
            
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