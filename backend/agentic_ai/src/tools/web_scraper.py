import json
import asyncio
from typing import Optional
from langchain_core.tools import tool
from loguru import logger

@tool
async def playwright_scrape(url: str, wait_until: str = "domcontentloaded", selector: Optional[str] = None) -> str:
    """
    <module_purpose>
    Scrape dynamic web content using Playwright headless browser.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this to extract text from websites that rely on JavaScript to render content.
    - If a normal HTTP GET request fails or returns no useful content.
    - `wait_until` options: 'load', 'domcontentloaded', 'networkidle'.
    - `selector`: If provided, only returns text from the specific CSS selector.
    </contract>
    """
    try:
        from src.core.delegation import delegator
        payload = {
            "url": url,
            "wait_until": wait_until,
            "selector": selector
        }
        result = await delegator.delegate("SCRAPE_URL", payload, timeout=30.0)
        return result
    except Exception as e:
        logger.exception(f"Web Scraper delegation failed for {url}")
        return json.dumps({"error": f"Delegation error: {str(e)}"})
