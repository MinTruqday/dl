import asyncio
import random
from contextlib import asynccontextmanager

import aiohttp
from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

ua = UserAgent(
    os=["windows", "macos"], browsers=["chrome", "edge", "firefox", "safari"]
)


@asynccontextmanager
async def managed_browser(headless=True):
    playwright = None
    browser = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-application-cache",
                "--mute-audio",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--js-flags=--max-old-space-size=4096",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )
        yield browser
    except Exception:
        logger.error("The automated browser environment failed to initialize or execute due to an underlying process configuration issue")
        raise
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                logger.warning("The background cleanup routine encountered a delay while attempting to safely close the automated browser instance")
        if playwright:
            try:
                await playwright.stop()
            except Exception:
                logger.warning("The background cleanup routine encountered a resource lock while attempting to terminate the rendering engine instance")


async def get_stealth_context(browser):
    context = await browser.new_context(
        user_agent=ua.random,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    return context


async def download_file_with_retry(
    url: str, dest_path: str, timeout: int = 300, max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 200:
                        with open(dest_path, "wb") as f:
                            while True:
                                chunk = await resp.content.read(65536)
                                if not chunk:
                                    break
                                f.write(chunk)
                        return True
                    else:
                        logger.error("The network request to the specified remote resource failed due to an unexpected hyper text transfer protocol status code")
        except Exception:
            logger.warning("A temporary network disruption occurred during the download process so the system is preparing an automated retry sequence")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
            else:
                logger.error("The remote file download process failed permanently because all automated retry attempts have been exhausted")
    return False