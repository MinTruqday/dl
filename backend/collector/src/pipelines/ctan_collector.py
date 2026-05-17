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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

class CTANCollector:
    @staticmethod
    async def run_list_collector():
        logger.info("Starting CTAN Alphabetical List Collector")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                for letter in string.ascii_uppercase:
                    search_url = f"https://www.ctan.org/pkg/:{letter}"
                    logger.info(f"Scanning CTAN Category: {letter} -> {search_url}")
                    
                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)
                    
                    list_xpath = 'xpath=/html/body/div[2]/main/div[1]/a'
                    
                    try:
                        await page.wait_for_selector('xpath=/html/body/div[2]/main/div[1]', timeout=15000)
                    except Exception as e:
                        logger.warning(f"Timeout or empty container for letter {letter}: {e}")
                        continue
                    
                    book_nodes = await page.query_selector_all(list_xpath)
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
            finally:
                await browser.close()

    @staticmethod
    async def run_detail_collector(book_url: str):
        logger.info(f"[Detail Collector] CTAN: {book_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                await page.goto(book_url, timeout=60000)
                await page.wait_for_timeout(2000)
                
                payload = {}
                payload["source_url"] = book_url
                
                title_xpath = 'xpath=/html/body/div[2]/main/h1'
                title_el = await page.query_selector(title_xpath)
                raw_title = await title_el.inner_text() if title_el else book_url.split("/")[-1]
                payload["title"] = raw_title.strip()
                
                desc_xpath = 'xpath=/html/body/div[2]/main/div[1]/p[2]'
                desc_el = await page.query_selector(desc_xpath)
                payload["description"] = await desc_el.inner_text() if desc_el else "No description available."
                
                author_xpath = 'xpath=/html/body/div[2]/main/div[1]/table/tbody/tr[6]/td[2]'
                author_el = await page.query_selector(author_xpath)
                authors_list = []
                if author_el:
                    raw_authors = await author_el.inner_text()
                    split_authors = re.split(r'\n|,', raw_authors)
                    authors_list = [a.strip() for a in split_authors if a.strip()]
                payload["authors"] = authors_list if authors_list else ["Unknown Author"]
                
                download_xpath = 'xpath=/html/body/div[2]/main/div[1]/p[4]/a'
                download_el = await page.query_selector(download_xpath)
                
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
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=300) as resp:
                    if resp.status == 200:
                        with open(target_zip_local, "wb") as f:
                            while True:
                                chunk = await resp.content.read(65536)
                                if not chunk:
                                    break
                                f.write(chunk)
                                
                        logger.info(f"[CTAN Stream] Downloaded to temp: {target_zip_local}")
                        
                        minio_url_book = await storage.upload_local_file(f"books/ctan/{filename}", target_zip_local)
                        
                        logger.info(f"Extracting ZIP archive...")
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
                        
                        logger.info(f"Successfully processed {filename}.")
                    else:
                        logger.error(f"[CTAN Download Error] Cannot get. Code: {resp.status} - {url}")
                        return
        except Exception as e:
            logger.error(f"[Aiohttp/Extraction Error]: {e}")
            return
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
                "tags": payload.get("authors", []),
                "content_format": "zip",
                "price": 0.0,
                "visibility": "public",
                "author_id": "ctan-crawler",
                "status": "published",
                "rag_status": "pending",
                "views": 0,
                "average_rating": 0.0
            }
            
            doc_id = await db_client.insert_document(book_document)
            if doc_id:
                await mq_client.publish("format_converter_queue", {"book_id": doc_id, "file_url": minio_url_book, "filename": filename})