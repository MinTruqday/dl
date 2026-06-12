import random
import aiohttp
import asyncio
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from loguru import logger

from fake_useragent import UserAgent
ua = UserAgent(os=['windows', 'macos'], browsers=['chrome', 'edge', 'firefox', 'safari'])

@asynccontextmanager
async def managed_browser(headless=True):
    playwright = None
    browser = None
    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-application-cache',
                '--mute-audio',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--js-flags=--max-old-space-size=4096',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        yield browser
    except Exception as e:
        logger.error(f"Lỗi trình duyệt: {e}")
        raise
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Lỗi lúc tắt trình duyệt: {e}")
        if playwright:
            try:
                await playwright.stop()
            except Exception as e:
                logger.warning(f"Lỗi lúc dừng playwright: {e}")

async def get_stealth_context(browser):
    context = await browser.new_context(
        user_agent=ua.random,
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True
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
                        logger.error(f"Mã lỗi: {resp.status} - {url}")
        except Exception as e:
            logger.warning(f"Lần thử thứ {attempt+1}/{max_retries} gặp sự cố với {url}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"Tải gặp sự cố xuống {url} sau {max_retries} lần thử")
    return False
