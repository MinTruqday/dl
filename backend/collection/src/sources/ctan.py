import os
import random
import re
import string
import urllib.parse
import zipfile
from pathlib import Path

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

class CtanSource:
    @staticmethod
    async def run_list_collector(letter: str = "a"):
        logger.info("[CTAN] Starting alphabetical list collection process")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                selected_letter = letter.upper()
                if selected_letter not in string.ascii_uppercase:
                    raise ValueError("Invalid CTAN letter")
                for current_letter in [selected_letter]:
                    search_url = f"https://www.ctan.org/pkg/:{current_letter}"
                    logger.info("[CTAN] Scanning alphabetical category")

                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)

                    list_css = 'main a[href*="/pkg/"]'

                    try:
                        await page.wait_for_selector("main", timeout=15000)
                    except Exception as e:
                        logger.exception("[CTAN] Documents not found in alphabetical category")
                        continue

                    book_nodes = await page.query_selector_all(list_css)
                    book_urls = set()

                    for node in book_nodes:
                        href = await node.get_attribute("href")
                        if href:
                            full_url = (
                                "https://www.ctan.org" + href
                                if href.startswith("/")
                                else href
                            )
                            book_urls.add(full_url)

                    logger.info("[CTAN] Category data collected")
                    for url in book_urls:
                        if not await dedup.is_collected("ctan_url", url):
                            await mq_client.publish(
                                "collect_detail_queue", {"url": url, "source": "CTAN"}
                            )
                            await dedup.mark_collected("ctan_url", url)

            except Exception as e:
                logger.exception("[CTAN] Failed to get alphabetical data list")
                raise

    @staticmethod
    async def run_detail_collector(book_url: str):
        logger.info("[CTAN] Processing software package data")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                await page.goto(book_url, timeout=60000)
                await page.wait_for_timeout(2000)

                payload = {}
                payload["source_url"] = book_url

                title_el = await page.query_selector("main h1")
                raw_title = (
                    await title_el.inner_text() if title_el else book_url.split("/")[-1]
                )
                payload["title"] = raw_title.strip()

                desc_el = await page.query_selector("main p")
                payload["description"] = (
                    await desc_el.inner_text()
                    if desc_el
                    else "No description available"
                )

                author_el = await page.query_selector(
                    'main table td a[href*="/author/"]'
                )
                authors_list = []
                if author_el:
                    raw_authors = await author_el.inner_text()
                    split_authors = re.split(r"\n|,", raw_authors)
                    authors_list = [a.strip() for a in split_authors if a.strip()]
                payload["authors"] = (
                    authors_list if authors_list else ["Unknown Author"]
                )

                download_el = await page.query_selector(
                    'main a[href$=".zip"], main a:has-text("Download")'
                )

                if download_el:
                    download_link = await download_el.get_attribute("href")
                    if download_link:
                        full_download_url = (
                            "https://www.ctan.org" + download_link
                            if download_link.startswith("/")
                            else download_link
                        )
                        payload["download_link"] = full_download_url

                        logger.info("[CTAN] Download URL created")

                        slug = urllib.parse.quote(
                            payload["title"].lower().replace(" ", "-"),
                            safe="",
                        )[:50]
                        payload["filename"] = f"{slug}.zip"
                        payload["content_format"] = "zip"

                        await mq_client.publish(
                            "download_processor_queue", {**payload, "source": "CTAN"}
                        )
                    else:
                        logger.warning("[CTAN] Download link contains no data")
                else:
                    logger.warning("[CTAN] Download button not found on page")

            except Exception as e:
                logger.exception("[CTAN] Compressed file data processing failed")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        import shutil
        import tempfile

        url = payload.get("download_link")
        title = payload.get("title", "package")

        if not url:
            logger.error("[CTAN] Invalid download URL")
            return

        logger.info("[CTAN] Downloading and extracting file")

        slug = urllib.parse.quote(title.lower().replace(" ", "-"), safe="")[:50]
        filename = payload.get("filename") or f"{slug}.zip"

        temp_base = tempfile.mkdtemp(prefix="ctan_")
        target_zip_local = os.path.join(temp_base, filename)
        extracted_folder_path = os.path.join(temp_base, "extracted", slug)

        minio_url_book = None

        try:
            success = await download_file_with_retry(url, target_zip_local)
            if success:
                logger.info("[CTAN] Compressed file downloaded")

                minio_url_book = await storage.upload_local_file(
                    f"system/collection/ctan/packages/{filename}", target_zip_local
                )

                logger.info("[CTAN] Extracting downloaded file")
                os.makedirs(extracted_folder_path, exist_ok=True)
                with zipfile.ZipFile(target_zip_local, "r") as zip_ref:
                    entries = zip_ref.infolist()
                    if len(entries) > 5000:
                        raise ValueError("Archive contains too many entries")
                    total_size = sum(entry.file_size for entry in entries)
                    if total_size > settings.MAX_DOWNLOAD_SIZE_BYTES:
                        raise ValueError("Extracted archive exceeds the configured size limit")
                    root = Path(extracted_folder_path).resolve()
                    for entry in entries:
                        target = (root / entry.filename).resolve()
                        if not target.is_relative_to(root):
                            raise ValueError("Archive contains an unsafe path")
                        mode = entry.external_attr >> 16
                        if mode & 0o170000 == 0o120000:
                            raise ValueError("Archive contains a symbolic link")
                    zip_ref.extractall(extracted_folder_path)

                search_root = extracted_folder_path
                contents = os.listdir(extracted_folder_path)
                if len(contents) == 1 and os.path.isdir(
                    os.path.join(extracted_folder_path, contents[0])
                ):
                    search_root = os.path.join(extracted_folder_path, contents[0])
                    logger.info("[CTAN] Processing compressed file directory structure")

                found_pdf = None
                for root, _, files in os.walk(search_root):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            if slug in f.lower() or "doc" in root.lower():
                                found_pdf = os.path.join(root, f)
                                break
                    if found_pdf:
                        break

                if found_pdf:
                    pdf_filename = os.path.basename(found_pdf)
                    minio_url_pdf = await storage.upload_local_file(
                        f"system/collection/ctan/documents/{pdf_filename}", found_pdf
                    )
                    logger.info("[CTAN] PDF file uploaded")
                    payload["pdf_url"] = minio_url_pdf

                md_content = f"# Source code for {title}\n\n"
                allowed_exts = {
                    ".tex",
                    ".sty",
                    ".cls",
                    ".dtx",
                    ".ins",
                    ".bib",
                    ".def",
                    ".pl",
                    ".txt",
                }
                for root_dir, _, files in os.walk(search_root):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in allowed_exts:
                            file_path = os.path.join(root_dir, f)
                            rel_path = os.path.relpath(file_path, search_root)
                            try:
                                with open(
                                    file_path, "r", encoding="utf-8"
                                ) as text_file:
                                    content = text_file.read()
                                    md_content += f"## File: {rel_path}\n```latex\n{content}\n```\n\n"
                            except UnicodeDecodeError:
                                continue
                            except Exception as e:
                                logger.exception("[CTAN] Nested file reading failed")

                md_filename = f"{slug}_source.md"
                md_path = os.path.join(temp_base, md_filename)
                with open(md_path, "w", encoding="utf-8") as md_f:
                    md_f.write(md_content)

                minio_url_md = await storage.upload_local_file(
                    f"system/collection/ctan/documents/{md_filename}", md_path
                )
                logger.info("[CTAN] Source code compiled and uploaded")
                payload["markdown_url"] = minio_url_md

                logger.info("[CTAN] Compressed file processed")
            else:
                logger.error("[CTAN] Compressed file download from remote server failed")
                return
        except Exception as e:
            logger.exception("[CTAN] Compressed file processing failed")
            raise
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)

        if minio_url_book:
            logger.info("[CTAN] Compressed file saved permanently")

            book_document = {
                "title": title,
                "slug": slug,
                "description": payload.get(
                    "description", "Trích xuất tự động hoàn tất"
                ),
                "file_url": minio_url_book,
                "source_url": payload.get("source_url"),
                "pdf_url": payload.get("pdf_url"),
                "markdown_url": payload.get("markdown_url"),
                "tags": ["CTAN"]
                + (payload.get("authors") if payload.get("authors") else ["Unknown"]),
                "content_format": "zip",
                "price": 0.0,
                "visibility": "private",
                "creator_id": "ctan",
                "status": "published",
                "rag_status": "pending",
                "views": 0,
            }

            doc_id = await database.insert_document(book_document)
