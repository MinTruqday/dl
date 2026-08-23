import asyncio
import ipaddress
import os
import socket
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import aiohttp
from fake_useragent import UserAgent
from loguru import logger
from playwright.async_api import async_playwright

from src.core.infrastructure.configuration import settings


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
        logger.exception("Automated browser initialization failed")
        raise
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                logger.exception("Automated browser cleanup failed")
        if playwright:
            try:
                await playwright.stop()
            except Exception:
                logger.exception("Browser runtime cleanup failed")


async def get_stealth_context(browser):
    return await browser.new_context(
        user_agent=ua.random, viewport={"width": 1920, "height": 1080}, ignore_https_errors=True
    )


async def validate_remote_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Invalid remote download URL")
    loop = asyncio.get_running_loop()
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = await loop.run_in_executor(None, lambda: socket.getaddrinfo(parsed.hostname, port))
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Remote download URL resolves to a restricted network")


async def download_file_with_retry(
    url: str, dest_path: str, timeout: int = 300, max_retries: int = 3
):
    await validate_remote_url(url)
    for attempt in range(max_retries):
        try:
            client_timeout = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Remote server returned status {response.status}")
                    content_length = int(response.headers.get("Content-Length", "0") or "0")
                    if content_length > settings.MAX_DOWNLOAD_SIZE_BYTES:
                        raise ValueError("Remote file exceeds the configured size limit")
                    total = 0
                    with open(dest_path, "wb") as stream:
                        while True:
                            chunk = await response.content.read(65536)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > settings.MAX_DOWNLOAD_SIZE_BYTES:
                                raise ValueError("Remote file exceeds the configured size limit")
                            stream.write(chunk)
                    if total < settings.MIN_FILE_SIZE_BYTES:
                        raise ValueError("Remote file is smaller than the configured minimum")
                    return True
        except Exception:
            logger.exception("Remote file download attempt failed")
            try:
                os.unlink(dest_path)
            except FileNotFoundError:
                logger.debug("No partial download file required cleanup")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
    return False
