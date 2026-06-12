from core.config import settings
import urllib.parse
import os
import aiohttp
import random
import requests
from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from loguru import logger
import tempfile

from src.core.mq import mq_client
from src.core.redis_client import dedup
from src.core.storage import storage
from src.core.db import db_client
from src.core.browser import managed_browser, get_stealth_context, download_file_with_retry

class AnnaArchiveCollector:
    @staticmethod
    async def run_list_collector(search_query: str = "", pages: int = 0):
        if search_query:
            logger.info(f"Bắt đầu tìm kiếm phân trang trên Anna's Archive: {search_query}")
        else:
            logger.info("Bắt đầu thu thập hàng loạt từ Anna's Archive")
        encoded = urllib.parse.quote(search_query)
        
        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                page_num = 1
                
                while True:
                    search_url = f"https://annas-archive.gl/search?index=journals&sort=&lang=en&lang=anti__zh&lang=la&lang=vi&display=&q={encoded}&page={page_num}"
                    logger.info(f"Đang chuyển sang trang {page_num}: {search_url}")
                    
                    await page.goto(search_url, timeout=60000, wait_until='domcontentloaded')
                    content = await page.content()
                    
                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("Trang tìm kiếm bị tường lửa chặn, đang thử dùng FlareSolverr")
                        flaresolverr_url = settings.FLARESOLVERR_URL
                        async with aiohttp.ClientSession() as session:
                            async with session.post(flaresolverr_url, json={"cmd": "request.get", "url": search_url, "maxTimeout": 60000}) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    resolved_content = data.get("solution", {}).get("response", "")
                                    if resolved_content:
                                        await page.set_content(resolved_content)
                    
                    list_selector = 'a[href*="/md5/"]'
                    try:
                        await page.wait_for_selector(list_selector, timeout=15000)
                    except Exception as e:
                        logger.error(f"Lỗi hoặc hết giờ khi đang lấy link MD5 ở trang {page_num}: {e}")
                    
                    document_nodes = await page.query_selector_all(list_selector)
                    if not document_nodes:
                        logger.warning(f"Trang này không có link MD5 {page_num}, nên dừng việc quét danh sách lại")
                        break
                    
                    document_urls = set()
                    for node in document_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = "https://annas-archive.gl" + href if href.startswith("/") else href
                            document_urls.add(full_url)
                    
                    logger.info(f"Lấy được {len(document_urls)} link MD5 ở trang {page_num}")
                    new_urls_found = 0
                    
                    for url in document_urls:
                        if not await dedup.is_collected("anna_url", url):
                            await mq_client.publish("collect_detail_queue", {"url": url})
                            await dedup.mark_collected("anna_url", url)
                            new_urls_found += 1
                    
                    logger.info(f"Vừa đẩy {new_urls_found} tài liệu mới từ trang {page_num} vào hàng đợi")
                    if page_num >= pages:
                        logger.info(f"Đã đủ số lượng {pages} trang yêu cầu, đang dừng tiến trình")
                        break
                    page_num += 1
            except Exception as e:
                logger.error(f"Quy trình lấy danh sách từ Anna's Archive gặp sự cố: {e}")

    @staticmethod
    async def get_flare_cleared_context(browser, url: str, logger):
        logger.info("Đang gọi FlareSolverr để lấy cookie và userAgent hợp lệ")
        try:
            flare_url = settings.FLARESOLVERR_URL
            async with aiohttp.ClientSession() as session:
                async with session.post(flare_url, json={"cmd": "request.get", "url": url, "maxTimeout": 60000}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sol = data.get("solution", {})
                        cookies = sol.get("cookies", [])
                        user_agent = sol.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
                        
                        context = await browser.new_context(user_agent=user_agent)
                        
                        formatted_cookies = []
                        for c in cookies:
                            formatted_cookies.append({
                                "name": c["name"],
                                "value": c["value"],
                                "domain": c["domain"],
                                "path": c["path"]
                            })
                        if formatted_cookies:
                            await context.add_cookies(formatted_cookies)
                        return context
        except Exception as e:
            logger.error(f"Không thể gọi FlareSolverr vì lỗi: {e}")
        return await get_stealth_context(browser)

    @staticmethod
    async def run_detail_collector(document_url: str):
        logger.info(f"Đang xử lý chi tiết sách Anna: {document_url}")
        
        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)
            
            try:
                await page.goto(document_url, timeout=60000)
                content = await page.content()
                
                if "DDoS-Guard" in content or "cloudflare" in content.lower():
                    logger.info("Trang chi tiết bị chặn, đang dùng FlareSolverr để vượt qua")
                    await page.close()
                    await context.close()
                    
                    context = await AnnaArchiveCollector.get_flare_cleared_context(browser, document_url, logger)
                    page = await context.new_page()
                    await stealth_async(page)
                    await page.goto(document_url, timeout=60000)
                
                payload = {}
                payload["source_url"] = document_url
                

                title_el = await page.query_selector('div.text-3xl.font-bold') or await page.query_selector('div.text-2xl.font-bold') or await page.query_selector('div.text-2xl.font-semibold')
                raw_title = await title_el.inner_text() if title_el else document_url.split("/")[-1]
                payload["title"] = raw_title
                

                author_el = await page.query_selector('div.italic')
                payload["author"] = await author_el.inner_text() if author_el else "Unknown"
                
                logger.info(f"Lấy thông tin sách: {payload['title']}, Author: {payload['author']}")
                
                cover_el = await page.query_selector('img[src*="covers/"]') or await page.query_selector('img[src*="isbn"]') or await page.query_selector('div > img')
                if cover_el:
                    cover_src = await cover_el.get_attribute("src")
                    if cover_src:
                        payload["cover_url"] = cover_src
                

                slow_link_css = 'a:has-text("Slow"), #md5-panel-downloads a[href*="/download"]'
                slow_link_el = await page.query_selector(slow_link_css)

                if slow_link_el:
                    slow_href = await slow_link_el.get_attribute("href")
                    slow_url = "https://annas-archive.gl" + slow_href if slow_href.startswith("/") else slow_href
                    logger.info(f"Đang mở trang chứa link tải: {slow_url}")
                    
                    await page.goto(slow_url, timeout=60000)
                    content = await page.content()
                    
                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("Trang tải bị chặn, đang dùng FlareSolverr để vượt qua")
                        await page.close()
                        await context.close()
                        
                        context = await AnnaArchiveCollector.get_flare_cleared_context(browser, slow_url, logger)
                        page = await context.new_page()
                        await stealth_async(page)
                        await page.goto(slow_url, timeout=60000)
                    
                    try:
                        download_link = None
                        js_link_css = 'main p a[href*="http"]'
                        
                        logger.info("Đang chờ bộ đếm thời gian JS chạy xong")
                        for _ in range(60):
                            try:
                                link_els = await page.query_selector_all(js_link_css)
                                for link_el in link_els:
                                    href = await link_el.get_attribute("href")
                                    if href and href.startswith("http") and "annas-archive" not in href:
                                        download_link = href
                                        break
                                if download_link:
                                    break
                            except Exception as parse_err:
                                logger.warning(f"Không thể lấy được link tải vì lỗi: {parse_err}")
                                
                            await page.wait_for_timeout(5000)

                        if download_link:
                            payload["download_link"] = download_link
                            logger.info(f"Đã lấy được link tải: {download_link}")
                            
                            ext = payload["download_link"].split('')[-1][:4] if '' in payload["download_link"].split('/')[-1] else 'pdf'
                            if len(ext) > 4 or "/" in ext: ext = 'pdf'
                            slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"))[:50]
                            payload["filename"] = f"{slug}.{ext}"
                            payload["content_format"] = ext
                            
                            await mq_client.publish("download_processor_queue", payload)
                        else:
                            logger.warning(f"Hết thời gian chờ xử lý đếm ngược bằng JS: {slow_url}")
                    except Exception as e:
                        logger.error(f"Chờ liên kết tải xuống gặp sự cố: {e}")
                if not slow_link_el:
                    logger.warning(f"Không tìm thấy nút tải trên trang: {document_url}")
                    await page.screenshot(path="/app/logs/anna_error.png", full_page=True)
                    links = await page.evaluate("Array.from(document.querySelectorAll('a, button')).map(el => el.innerText.trim()).filter(t => t.length > 0)")
                    logger.warning(f"Các nút có thể bấm được trên trang: {links}")
                    await page.close()
                    raise Exception("Không tìm thấy nút tải chậm")
            except Exception as e:
                logger.error(f"Gặp lỗi: {e}")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        url = payload.get("download_link")
        title = payload.get("title", "document")
        
        if not url:
            logger.error(f"URL tải trọng không hợp lệ: {title}")
            return
            
        logger.info(f"Đang tải file sách: {title}")
        
        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        ext = payload.get("content_format", "pdf")
        filename = payload.get("filename") or f"{slug}.{ext}"
        
        minio_url = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                target_local = tmp_file.name
                
            success = await download_file_with_retry(url, target_local)
            if success:
                logger.info(f"Đã tải về tệp tạm thời {target_local}")
                minio_url = await storage.upload_local_file(f"tài liệu/anna_archive/{filename}", target_local)
                
            if os.path.exists(target_local):
                os.unlink(target_local)
        except Exception as e:
            logger.error(f"Gặp lỗi: {e}")
            raise
            
        if minio_url:
            logger.info(f"Tài liệu đã được lưu lên hệ thống lưu trữ: {minio_url}")
            
            document_metadata = {
                "title": title,
                "slug": slug,
                "description": f"Đã trích xuất via Anna's Archive bot",
                "file_url": minio_url,
                "pdf_url": minio_url if ext.lower() == "pdf" else None,
                "tags": ["Anna's Archive", payload.get("author", "Unknown")],
                "content": None,
                "content_format": ext,
                "price": 0.0,
                "visibility": "public",
                "author_id": "annas-archive",
                "status": "published",
                "views": 0,
                "average_rating": 0.0
            }
            
            doc_id = await db_client.insert_document(document_metadata)
