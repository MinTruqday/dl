import asyncio
from contextlib import asynccontextmanager
import aiohttp
from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

ua = UserAgent(os=["windows", "macos"], browsers=["chrome", "edge", "firefox", "safari"])

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
        logger.error("Automated structural browser environment failed initializing safely executing underlying process system configuration issue")
        raise
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                logger.warning("Background cleanup operational routine encountered unexpected delay safely closing functional automated browser instance")
        if playwright:
            try:
                await playwright.stop()
            except Exception:
                logger.warning("Background cleanup structural routine encountered resource lock actively attempting terminate primary rendering engine")

async def get_stealth_context(browser):
    context = await browser.new_context(
        user_agent=ua.random,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    return context

async def download_file_with_retry(url: str, dest_path: str, timeout: int = 300, max_retries: int = 3):
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
                        logger.error("Network transfer request specified remote structural resource failed unexpected operational protocol numeric status code")
        except Exception:
            logger.warning("Temporary dynamic network disruption occurred processing active download system preparing automated retry functional sequence")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
            else:
                logger.error("Remote file download operational process failed permanently exhausted all configured automated structural retry attempts")
    return False