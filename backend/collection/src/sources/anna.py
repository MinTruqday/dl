import os
import random
import re
import tempfile
import urllib.parse

import aiohttp
import requests
from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from src.infrastructure.browser import (
    download_file_with_retry,
    get_stealth_context,
    managed_browser,
)
from src.core.database import database
from src.core.infrastructure.mq import mq as mq_client
from src.core.cache import dedup
from src.core.storage import storage

from src.core.infrastructure.configuration import settings

class AnnaSource:
    @staticmethod
    async def run_list_collector(search_query: str = "", pages: int = 0):
        if search_query:
            logger.info("[AnnaSource] Searching information from external source")
        else:
            logger.info("[AnnaSource] Starting bulk data collection process")
        encoded = urllib.parse.quote(search_query)

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                page_num = 1

                while True:
                    search_url = f"https://annas-archive.gl/search?index=journals&sort=&lang=en&lang=anti__zh&lang=la&lang=vi&display=&q={encoded}&page={page_num}"
                    logger.info("[AnnaSource] Navigating to next results page")

                    await page.goto(
                        search_url, timeout=60000, wait_until="domcontentloaded"
                    )
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("[AnnaSource] Firewall protection detected")
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
                    except Exception as e:
                        logger.exception("[AnnaSource] Link extraction failed due to UI changes")

                    document_nodes = await page.query_selector_all(list_selector)
                    if not document_nodes:
                        logger.warning(
                            "[AnnaSource] No document links found, stopping list scan"
                        )
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

                    logger.info("[AnnaSource] Document links extracted successfully")
                    new_urls_found = 0

                    for url in document_urls:
                        if not await dedup.is_collected("anna_url", url):
                            await mq_client.publish(
                                "collect_detail_queue", {"url": url}
                            )
                            await dedup.mark_collected("anna_url", url)
                            new_urls_found += 1

                    logger.info("[AnnaSource] Document links added to queue successfully")
                    if page_num >= pages:
                        logger.info("[AnnaSource] Page limit reached, stopping scan")
                        break
                    page_num += 1
            except Exception as e:
                logger.exception("[AnnaSource] Failed to load document list from external source")

    @staticmethod
    async def get_flare_cleared_context(browser, url: str, logger):
        logger.info("[AnnaSource] Retrieving valid session information")
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
        except Exception as e:
            logger.exception("[AnnaSource] Firewall bypass failed")
        return await get_stealth_context(browser)

    @staticmethod
    async def run_detail_collector(document_url: str):
        logger.info("[AnnaSource] Processing detailed document information")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(document_url, timeout=60000)
                content = await page.content()

                if "DDoS-Guard" in content or "cloudflare" in content.lower():
                    logger.info("[AnnaSource] Document is protected, processing access bypass")
                    await page.close()
                    await context.close()

                    context = await AnnaSource.get_flare_cleared_context(
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

                logger.info("[AnnaSource] Document information extracted successfully")

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
                    logger.info("[AnnaSource] Accessing download gateway")

                    await page.goto(slow_url, timeout=60000)
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("[AnnaSource] Firewall detected at download gateway, processing bypass")
                        await page.close()
                        await context.close()

                        context = await AnnaSource.get_flare_cleared_context(
                            browser, slow_url, logger
                        )
                        page = await context.new_page()
                        await stealth_async(page)
                        await page.goto(slow_url, timeout=60000)

                    try:
                        download_link = None
                        js_link_css = 'main p a[href*="http"]'

                        logger.info("[AnnaSource] Waiting for security verification")
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
                            except Exception as e:
                                logger.exception("[AnnaSource] Download link extraction failed")

                            await page.wait_for_timeout(5000)

                        if download_link:
                            payload["download_link"] = download_link
                            logger.info("[AnnaSource] Download link extracted successfully")

                            parsed_path = urllib.parse.urlparse(payload["download_link"]).path
                            ext = os.path.splitext(parsed_path)[1].lstrip(".").lower() or "pdf"
                            if not re.fullmatch(r"[a-z0-9]{1,8}", ext):
                                ext = "pdf"
                            slug = urllib.parse.quote(
                                payload["title"].lower().replace(" ", "-"),
                                safe="",
                            )[:50]
                            payload["filename"] = f"{slug}.{ext}"
                            payload["content_format"] = ext

                            await mq_client.publish("download_processor_queue", payload)
                        else:
                            logger.warning("[AnnaSource] Security verification timeout")
                    except Exception as e:
                        logger.exception("[AnnaSource] Error monitoring download link generation")
                if not slow_link_el:
                    logger.warning("[AnnaSource] Download button not found")
                    await page.screenshot(
                        path="/app/logs/anna_error.png", full_page=True
                    )
                    links = await page.evaluate(
                        "Array.from(document.querySelectorAll('a, button')).map(el => el.innerText.trim()).filter(t => t.length > 0)"
                    )
                    logger.warning("[AnnaSource] Recording page elements for debugging")
                    await page.close()
                    raise RuntimeError("Download link not found")
            except Exception as e:
                logger.exception("[AnnaSource] Document extraction failed")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        url = payload.get("download_link")
        title = payload.get("title", "document")

        if not url:
            logger.error("[AnnaSource] Invalid download URL")
            return

        logger.info("[AnnaSource] Downloading document to temporary storage")

        slug = urllib.parse.quote(title.lower().replace(" ", "-"), safe="")[:50]
        ext = payload.get("content_format", "pdf")
        filename = payload.get("filename") or f"{slug}.{ext}"

        minio_url = None

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                target_local = tmp_file.name

            success = await download_file_with_retry(url, target_local)
            if success:
                logger.info("[AnnaSource] Document downloaded successfully")
                minio_url = await storage.upload_local_file(
                    f"system/collection/anna_archive/{filename}", target_local
                )

            if os.path.exists(target_local):
                os.unlink(target_local)
        except Exception as e:
            logger.exception("[AnnaSource] Document download and storage failed")
            raise

        if minio_url:
            logger.info("[AnnaSource] Downloaded document transferred to permanent storage successfully")

            metadata = {
                "title": title,
                "slug": slug,
                "description": "Trích xuất tự động hoàn tất",
                "file_url": minio_url,
                "source_url": payload.get("source_url"),
                "pdf_url": minio_url if ext.lower() == "pdf" else None,
                "tags": ["AnnaSource's Archive", payload.get("author", "Unknown")],
                "content": None,
                "content_format": ext,
                "price": 0.0,
                "visibility": "public",
                "creator_id": "annas-archive",
                "status": "published",
                "views": 0,
            }

            doc_id = await database.insert_document(metadata)
