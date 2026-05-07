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
logger.info("Log message sanitized"))
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            await stealth_async(page)
            try:
                for letter in string.ascii_uppercase:
                    search_url = f"https://www.ctan.org/pkg/:{letter}"
logger.info("Log message sanitized"))
                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)
                    list_xpath = 'xpath=/html/body/div[2]/main/div[1]/a'
                    try:
                        await page.wait_for_selector('xpath=/html/body/div[2]/main/div[1]', timeout=15000)
                    except Exception as e:
logger.info("Log message sanitized"))
                        continue
                    book_nodes = await page.query_selector_all(list_xpath)
                    book_urls = set()
                    for node in book_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = "https://www.ctan.org" + href if href.startswith("/") else href
                            book_urls.add(full_url)
logger.info("Log message sanitized"))
                    for url in book_urls:
                        if not await dedup.is_collected("ctan_url", url):
                            await mq_client.publish("collect_detail_queue", {"url": url, "source": "CTAN"})
                            await dedup.mark_collected("ctan_url", url)
            except Exception as e:
logger.info("Log message sanitized"))
            finally:
                await browser.close()
    @staticmethod
    async def run_detail_collector(book_url: str):
logger.info("Log message sanitized"))
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
logger.info("Log message sanitized"))
                        slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"))[:50]
                        payload["filename"] = f"{slug}.zip"
                        payload["content_format"] = "zip"
                        await mq_client.publish("download_processor_queue", {**payload, "source": "CTAN"})
                    else:
logger.info("Log message sanitized"))
                else:
logger.info("Log message sanitized"))
            except Exception as e:
logger.info("Log message sanitized"))
            finally:
                await browser.close()
    @staticmethod
    async def run_download_processor(payload: dict):
        url = payload.get("download_link")
        title = payload.get("title", "package")
        if not url:
logger.info("Log message sanitized"))
            return
logger.info("Log message sanitized"))
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        filename = payload.get("filename") or f"{slug}.zip"
        os.makedirs("/app/books/ctan/zips", exist_ok=True)
        os.makedirs("/app/books/ctan/extracted", exist_ok=True)
        target_zip_local = f"/app/books/ctan/zips/{filename}"
        extracted_folder_path = f"/app/books/ctan/extracted/{slug}"
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
logger.info("Log message sanitized"))
                        minio_url_book = await storage.upload_local_file(f"books/ctan/{filename}", target_zip_local)
logger.info("Log message sanitized"))
                        os.makedirs(extracted_folder_path, exist_ok=True)
                        with zipfile.ZipFile(target_zip_local, 'r') as zip_ref:
                            zip_ref.extractall(extracted_folder_path)
logger.info("Log message sanitized"))
                    else:
logger.info("Log message sanitized"))
                        return
        except Exception as e:
logger.info("Log message sanitized"))
            return
        if minio_url_book:
logger.info("Log message sanitized"))
            book_document = {
                "title": title,
                "slug": slug,
                "description": payload.get("description", "Extracted via CTAN bot."),
                "file_url": minio_url_book,
                "tags": payload.get("authors", []),
                "contents": extracted_folder_path, 
                "content_format": "zip",
                "price": 0.0,
                "visibility": "public",
                "author_id": "ctan-crawler",
                "status": "published",
                "views": 0,
                "average_rating": 0.0
            }
            doc_id = await db_client.insert_document(book_document)
            if doc_id:
                await mq_client.publish("format_converter_queue", {"book_id": doc_id, "file_url": minio_url_book, "filename": filename, "contents_path": extracted_folder_path})