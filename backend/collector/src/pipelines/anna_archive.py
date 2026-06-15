import os
import urllib.parse
import aiohttp
import tempfile
from core.config import settings
from loguru import logger
from playwright_stealth import stealth_async
from src.core.browser import download_file_with_retry, get_stealth_context, managed_browser
from src.core.db import db_client
from src.core.mq import mq_client
from src.core.redis import dedup
from src.core.storage import storage

class AnnaArchivePipeline:
    
    @staticmethod
    async def collect_list(search_query: str = "", pages: int = 0):
        if search_query:
            logger.info("System initiating paginated search operation on specified external data source")
        else:
            logger.info("System initiating comprehensive bulk data collection process across primary archives")
            
        encoded = urllib.parse.quote(search_query)

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                page_num = 1
                while True:
                    search_url = f"https://annas-archive.gl/search?index=journals&sort=&lang=en&lang=anti__zh&lang=la&lang=vi&display=&q={encoded}&page={page_num}"
                    logger.info("Collection bot navigating to next paginated section of external search results")

                    await page.goto(search_url, timeout=60000, wait_until="domcontentloaded")
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("Active firewall protection detected so system engaging automated evasion mechanisms")
                        flaresolverr_url = settings.FLARESOLVERR_URL
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                flaresolverr_url,
                                json={"cmd": "request.get", "url": search_url, "maxTimeout": 60000},
                            ) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    resolved_content = data.get("solution", {}).get("response", "")
                                    if resolved_content:
                                        await page.set_content(resolved_content)

                    list_selector = 'a[href*="/md5/"]'
                    try:
                        await page.wait_for_selector(list_selector, timeout=15000)
                    except Exception:
                        logger.error("Collection bot failed to extract document reference links due to unexpected layout changes")

                    document_nodes = await page.query_selector_all(list_selector)
                    if not document_nodes:
                        logger.warning("No valid document reference links found on current page so scanning process halting")
                        break

                    document_urls = set()
                    for node in document_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = "https://annas-archive.gl" + href if href.startswith("/") else href
                            document_urls.add(full_url)

                    logger.info("Collection bot successfully extracted available document reference links from current index page")

                    for url in document_urls:
                        if not await dedup.is_collected("anna_url", url):
                            await mq_client.publish("collect_detail_queue", {"url": url})
                            await dedup.mark_collected("anna_url", url)

                    logger.info("Newly discovered document links successfully placed into distributed processing queue")
                    if page_num >= pages:
                        logger.info("Maximum allowed page count reached so list scanning process is halting successfully")
                        break
                    page_num += 1
            except Exception:
                logger.error("System failed to retrieve document list from external source due to network failure")

    @staticmethod
    async def get_flare_cleared_context(browser, url: str):
        logger.info("Collection bot requesting valid session tokens and secure agent profiles from evasion service")
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
                        formatted_cookies = [
                            {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c["path"]}
                            for c in cookies
                        ]
                        if formatted_cookies:
                            await context.add_cookies(formatted_cookies)
                        return context
        except Exception:
            logger.error("Automated request to evasion service failed to return valid cryptographic clearance token")
        return await get_stealth_context(browser)

    @staticmethod
    async def collect_detail(document_url: str):
        logger.info("Collection bot currently processing detailed structural metadata for specified archival document")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(document_url, timeout=60000)
                content = await page.content()

                if "DDoS-Guard" in content or "cloudflare" in content.lower():
                    logger.info("Detailed document page protected by firewall so system engaging active evasion mechanisms")
                    await page.close()
                    await context.close()

                    context = await AnnaArchivePipeline.get_flare_cleared_context(browser, document_url)
                    page = await context.new_page()
                    await stealth_async(page)
                    await page.goto(document_url, timeout=60000)

                payload = {"source_url": document_url}

                title_el = (
                    await page.query_selector("div.text-3xl.font-bold")
                    or await page.query_selector("div.text-2xl.font-bold")
                    or await page.query_selector("div.text-2xl.font-semibold")
                )
                raw_title = await title_el.inner_text() if title_el else document_url.split("/")[-1]
                payload["title"] = raw_title

                author_el = await page.query_selector("div.italic")
                payload["author"] = await author_el.inner_text() if author_el else "Unknown"

                logger.info("Essential document metadata successfully extracted from external archival source page")

                cover_el = (
                    await page.query_selector('img[src*="covers/"]')
                    or await page.query_selector('img[src*="isbn"]')
                    or await page.query_selector("div > img")
                )
                if cover_el:
                    cover_src = await cover_el.get_attribute("src")
                    if cover_src:
                        payload["cover_url"] = cover_src

                slow_link_css = 'a:has-text("Slow"), #md5-panel-downloads a[href*="/download"]'
                slow_link_el = await page.query_selector(slow_link_css)

                if slow_link_el:
                    slow_href = await slow_link_el.get_attribute("href")
                    slow_url = "https://annas-archive.gl" + slow_href if slow_href.startswith("/") else slow_href
                    logger.info("Collection bot navigating to secure download gateway for current specific document")

                    await page.goto(slow_url, timeout=60000)
                    content = await page.content()

                    if "DDoS-Guard" in content or "cloudflare" in content.lower():
                        logger.info("Secure download gateway protected by firewall so system engaging active evasion mechanisms")
                        await page.close()
                        await context.close()

                        context = await AnnaArchivePipeline.get_flare_cleared_context(browser, slow_url)
                        page = await context.new_page()
                        await stealth_async(page)
                        await page.goto(slow_url, timeout=60000)

                    try:
                        download_link = None
                        js_link_css = 'main p a[href*="http"]'

                        logger.info("Collection bot waiting for external security timer to complete its active validation cycle")
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
                            except Exception:
                                logger.warning("Collection bot encountered difficulties attempting to extract secure download endpoint link")

                            await page.wait_for_timeout(5000)

                        if download_link:
                            payload["download_link"] = download_link
                            logger.info("Secure download link successfully extracted and validated against security protocol")

                            ext = payload["download_link"].split("")[-1][:4] if "" in payload["download_link"].split("/")[-1] else "pdf"
                            if len(ext) > 4 or "/" in ext:
                                ext = "pdf"
                            slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"))[:50]
                            payload["filename"] = f"{slug}.{ext}"
                            payload["content_format"] = ext

                            await mq_client.publish("download_processor_queue", payload)
                        else:
                            logger.warning("Security timer execution exceeded maximum allowed waiting period and timed out automatically")
                    except Exception:
                        logger.error("Unexpected error occurred while system was monitoring download link generation process")
                if not slow_link_el:
                    logger.warning("Required download action button could not be located on active document page")
                    raise Exception("Automated collection process could not locate valid download button on provided source page")
            except Exception:
                logger.error("Unexpected system error occurred during detailed document extraction and parsing process")
                raise

    @staticmethod
    async def process_download(payload: dict):
        url = payload.get("download_link")
        title = payload.get("title", "document")

        if not url:
            logger.error("Provided download link structurally invalid and cannot be processed by background downloader")
            return

        logger.info("System currently downloading requested document file into local secure temporary storage buffer")

        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        ext = payload.get("content_format", "pdf")
        filename = payload.get("filename") or f"{slug}.{ext}"

        minio_url = None

        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                target_local = tmp_file.name

            success = await download_file_with_retry(url, target_local)
            if success:
                logger.info("Remote document successfully downloaded and securely saved to temporary system storage path")
                minio_url = await storage.upload_local_file(f"documents/anna_archive/{filename}", target_local)

            if os.path.exists(target_local):
                os.unlink(target_local)
        except Exception:
            logger.error("Unexpected system error occurred attempting to download and save remote document file")
            raise

        if minio_url:
            logger.info("Downloaded document successfully transferred to permanent enterprise object storage backend system")

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

            await db_client.insert_document(document_metadata)