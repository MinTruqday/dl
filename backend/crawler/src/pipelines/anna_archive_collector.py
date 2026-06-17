import os
import random
import re
import tempfile
import urllib.parse

import aiohttp
import requests
from bs4 import BeautifulSoup
from core.config import settings
from loguru import logger
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from src.core.browser import (
    download_file_with_retry,
    get_stealth_context,
    managed_browser,
)
from src.core.db import db_client
from src.core.mq import mq_client
from src.core.redis_client import dedup
from src.core.storage import storage


class AnnaArchiveCollector:
    @staticmethod
    async def run_list_collector(search_query: str = "", pages: int = 0):
        if search_query:
            logger.info("The system is initiating a paginated search operation on the specified external data source")
        else:
            logger.info("The system is initiating a comprehensive bulk data collection process")
        encoded = urllib.parse.quote(search_query)

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                page_num = 1

                while True:
                    search_url = f"https://annas-archive.gl/search?index=journals&sort=&lang=en&lang=anti__zh&lang=la&lang=vi&display=&q={encoded}&page={page_num}"
                    logger.info("The collection bot is currently navigating to the next paginated section of the search results")

                    await page.goto(
                        search_url, timeout=60000, wait_until="domcontentloaded"
                    )
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("An active firewall protection layer was detected so the system is engaging its automated evasion mechanisms")
                        flaresolverr_url = settings.FLARESOLVERR_URL
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                flaresolverr_url,
                                json={
                                    "cmd": "request.get",
                                    "url": search_url,
                                    "maxTimeout": 60000,
                                },
                            ) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    resolved_content = data.get("solution", {}).get(
                                        "response", ""
                                    )
                                    if resolved_content:
                                        await page.set_content(resolved_content)

                    list_selector = 'a[href*="/md5/"]'
                    try:
                        await page.wait_for_selector(list_selector, timeout=15000)
                    except Exception:
                        logger.error("The collection bot failed to extract document reference links from the current page due to an unexpected layout change")

                    document_nodes = await page.query_selector_all(list_selector)
                    if not document_nodes:
                        logger.warning("No valid document reference links were found on the current page so the list scanning process is halting")
                        break

                    document_urls = set()
                    for node in document_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = (
                                "https://annas-archive.gl" + href
                                if href.startswith("/")
                                else href
                            )
                            document_urls.add(full_url)

                    logger.info("The collection bot has successfully extracted the available document reference links from the current page")
                    new_urls_found = 0

                    for url in document_urls:
                        if not await dedup.is_collected("anna_url", url):
                            await mq_client.publish(
                                "collect_detail_queue", {"url": url}
                            )
                            await dedup.mark_collected("anna_url", url)
                            new_urls_found += 1

                    logger.info("The newly discovered document links have been successfully placed into the processing queue")
                    if page_num >= pages:
                        logger.info("The maximum allowed page count has been reached so the list scanning process is successfully halting")
                        break
                    page_num += 1
            except Exception:
                logger.error("The system failed to retrieve the document list from the external source due to a network or parsing failure")

    @staticmethod
    async def get_flare_cleared_context(browser, url: str, logger):
        logger.info("The collection bot is actively requesting valid session tokens and secure agent profiles from the evasion service")
        try:
            flare_url = settings.FLARESOLVERR_URL
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    flare_url,
                    json={"cmd": "request.get", "url": url, "maxTimeout": 60000},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sol = data.get("solution", {})
                        cookies = sol.get("cookies", [])
                        user_agent = sol.get(
                            "user_agent",
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        )

                        context = await browser.new_context(user_agent=user_agent)

                        formatted_cookies = []
                        for c in cookies:
                            formatted_cookies.append(
                                {
                                    "name": c["name"],
                                    "value": c["value"],
                                    "domain": c["domain"],
                                    "path": c["path"],
                                }
                            )
                        if formatted_cookies:
                            await context.add_cookies(formatted_cookies)
                        return context
        except Exception:
            logger.error("The automated request to the evasion service failed to return a valid clearance token")
        return await get_stealth_context(browser)

    @staticmethod
    async def run_detail_collector(document_url: str):
        logger.info("The collection bot is currently processing the detailed metadata for the specified document")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(document_url, timeout=60000)
                content = await page.content()

                if "DDoS-Guard" in content or "cloudflare" in content.lower():
                    logger.info("The detailed document page is protected by a firewall so the system is engaging evasion mechanisms")
                    await page.close()
                    await context.close()

                    context = await AnnaArchiveCollector.get_flare_cleared_context(
                        browser, document_url, logger
                    )
                    page = await context.new_page()
                    await stealth_async(page)
                    await page.goto(document_url, timeout=60000)

                payload = {}
                payload["source_url"] = document_url

                title_el = (
                    await page.query_selector("div.text-3xl.font-bold")
                    or await page.query_selector("div.text-2xl.font-bold")
                    or await page.query_selector("div.text-2xl.font-semibold")
                )
                raw_title = (
                    await title_el.inner_text()
                    if title_el
                    else document_url.split("/")[-1]
                )
                payload["title"] = raw_title

                author_el = await page.query_selector("div.italic")
                payload["author"] = (
                    await author_el.inner_text() if author_el else "Unknown"
                )

                logger.info("The essential document metadata has been successfully extracted from the external source page")

                cover_el = (
                    await page.query_selector('img[src*="covers/"]')
                    or await page.query_selector('img[src*="isbn"]')
                    or await page.query_selector("div > img")
                )
                if cover_el:
                    cover_src = await cover_el.get_attribute("src")
                    if cover_src:
                        payload["cover_url"] = cover_src

                slow_link_css = (
                    'a:has-text("Slow"), #md5-panel-downloads a[href*="/download"]'
                )
                slow_link_el = await page.query_selector(slow_link_css)

                if slow_link_el:
                    slow_href = await slow_link_el.get_attribute("href")
                    slow_url = (
                        "https://annas-archive.gl" + slow_href
                        if slow_href.startswith("/")
                        else slow_href
                    )
                    logger.info("The collection bot is navigating to the secure download gateway for the current document")

                    await page.goto(slow_url, timeout=60000)
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("The secure download gateway is protected by a firewall so the system is engaging evasion mechanisms")
                        await page.close()
                        await context.close()

                        context = await AnnaArchiveCollector.get_flare_cleared_context(
                            browser, slow_url, logger
                        )
                        page = await context.new_page()
                        await stealth_async(page)
                        await page.goto(slow_url, timeout=60000)

                    try:
                        download_link = None
                        js_link_css = 'main p a[href*="http"]'

                        logger.info("The collection bot is waiting for the external security timer to complete its validation cycle")
                        for _ in range(60):
                            try:
                                link_els = await page.query_selector_all(js_link_css)
                                for link_el in link_els:
                                    href = await link_el.get_attribute("href")
                                    if (
                                        href
                                        and href.startswith("http")
                                        and "annas-archive" not in href
                                    ):
                                        download_link = href
                                        break
                                if download_link:
                                    break
                            except Exception:
                                logger.warning("The collection bot encountered difficulties while attempting to extract the secure download link")

                            await page.wait_for_timeout(5000)

                        if download_link:
                            payload["download_link"] = download_link
                            logger.info("The secure download link has been successfully extracted and validated")

                            ext = (
                                payload["download_link"].split("")[-1][:4]
                                if "" in payload["download_link"].split("/")[-1]
                                else "pdf"
                            )
                            if len(ext) > 4 or "/" in ext:
                                ext = "pdf"
                            slug = urllib.parse.quote(
                                payload["title"].lower().replace(" ", "-")
                            )[:50]
                            payload["filename"] = f"{slug}.{ext}"
                            payload["content_format"] = ext

                            await mq_client.publish("download_processor_queue", payload)
                        else:
                            logger.warning("The security timer execution exceeded the maximum allowed waiting period and timed out")
                    except Exception:
                        logger.error("An unexpected error occurred while the system was monitoring the download link generation process")
                if not slow_link_el:
                    logger.warning("The required download action button could not be located on the current document page")
                    await page.screenshot(
                        path="/app/logs/anna_error.png", full_page=True
                    )
                    links = await page.evaluate(
                        "Array.from(document.querySelectorAll('a, button')).map(el => el.innerText.trim()).filter(t => t.length > 0)"
                    )
                    logger.warning("The collection bot is logging the available actionable elements on the page for debugging purposes")
                    await page.close()
                    raise Exception("The automated collection process could not locate a valid download button on the provided page")
            except Exception:
                logger.error("An unexpected system error occurred during the detailed document extraction process")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        url = payload.get("download_link")
        title = payload.get("title", "document")

        if not url:
            logger.error("The provided download link is structurally invalid and cannot be processed by the downloader")
            return

        logger.info("The system is currently downloading the requested document file into temporary storage")

        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        ext = payload.get("content_format", "pdf")
        filename = payload.get("filename") or f"{slug}.{ext}"

        minio_url = None

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                target_local = tmp_file.name

            success = await download_file_with_retry(url, target_local)
            if success:
                logger.info("The remote document has been successfully downloaded and securely saved to the temporary storage path")
                minio_url = await storage.upload_local_file(
                    f"documents/anna_archive/{filename}", target_local
                )

            if os.path.exists(target_local):
                os.unlink(target_local)
        except Exception:
            logger.error("An unexpected system error occurred while attempting to download and save the document file")
            raise

        if minio_url:
            logger.info("The downloaded document has been successfully transferred to the permanent object storage system")

            document_metadata = {
                "title": title,
                "slug": slug,
                "description": "Extracted via automated collection process",
                "file_url": minio_url,
                "pdf_url": minio_url if ext.lower() == "pdf" else None,
                "tags": ["Anna's Archive", payload.get("author", "Unknown")],
                "content": None,
                "content_format": ext,
                "price": 0.0,
                "visibility": "public",
                "creator_id": "annas-archive",
                "status": "published",
                "views": 0,
                "average_rating": 0.0,
            }

            doc_id = await db_client.insert_document(document_metadata)