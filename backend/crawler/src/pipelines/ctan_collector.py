import os
import random
import re
import string
import urllib.parse
import zipfile

import aiohttp
import requests
from bs4 import BeautifulSoup
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


class CTANCollector:
    @staticmethod
    async def run_list_collector(pages: int = 0):
        logger.info("The system is initiating the automated alphabetical list collection process")

        async with managed_browser() as browser:
            context = await get_stealth_context(browser)
            page = await context.new_page()
            await stealth_async(page)

            try:
                for letter in string.ascii_uppercase:
                    search_url = f"https://www.ctan.org/pkg/:{letter}"
                    logger.info("The collection bot is currently scanning the selected alphabetical category index")

                    await page.goto(search_url, timeout=60000)
                    await page.wait_for_timeout(2000)

                    list_css = 'main a[href*="/pkg/"]'

                    try:
                        await page.wait_for_selector("main", timeout=15000)
                    except Exception:
                        logger.warning("The collection bot did not find any valid document entries within the current alphabetical category")
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

                    logger.info("The collection bot has successfully gathered the available package references for the current category")
                    for url in book_urls:
                        if not await dedup.is_collected("ctan_url", url):
                            await mq_client.publish(
                                "collect_detail_queue", {"url": url, "source": "CTAN"}
                            )
                            await dedup.mark_collected("ctan_url", url)

            except Exception:
                logger.error("An unexpected network or parsing error occurred during the alphabetical list collection process")
                raise

    @staticmethod
    async def run_detail_collector(book_url: str):
        logger.info("The collection bot is currently processing the detailed metadata for the specified software package")

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

                        logger.info("The secure download link for the software package has been successfully extracted")

                        slug = urllib.parse.quote(
                            payload["title"].lower().replace(" ", "-")
                        )[:50]
                        payload["filename"] = f"{slug}.zip"
                        payload["content_format"] = "zip"

                        await mq_client.publish(
                            "download_processor_queue", {**payload, "source": "CTAN"}
                        )
                    else:
                        logger.warning("The extraction process found an empty download link on the current package details page")
                else:
                    logger.warning("The required download action button could not be located on the software package page")

            except Exception:
                logger.error("An unexpected system error occurred while attempting to parse the software package metadata")
                raise

    @staticmethod
    async def run_download_processor(payload: dict):
        import shutil
        import tempfile

        url = payload.get("download_link")
        title = payload.get("title", "package")

        if not url:
            logger.error("The provided download link for the package archive is structurally invalid and cannot be processed")
            return

        logger.info("The system is currently downloading and preparing to extract the requested package archive")

        slug = urllib.parse.quote(title.lower().replace(" ", "-"))[:50]
        filename = payload.get("filename") or f"{slug}.zip"

        temp_base = tempfile.mkdtemp(prefix="ctan_")
        target_zip_local = os.path.join(temp_base, filename)
        extracted_folder_path = os.path.join(temp_base, "extracted", slug)

        minio_url_book = None

        try:
            success = await download_file_with_retry(url, target_zip_local)
            if success:
                logger.info("The remote package archive has been successfully downloaded to the temporary workspace")

                minio_url_book = await storage.upload_local_file(
                    f"books/ctan/{filename}", target_zip_local
                )

                logger.info("The background worker is currently extracting the contents of the downloaded package archive")
                os.makedirs(extracted_folder_path, exist_ok=True)
                with zipfile.ZipFile(target_zip_local, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder_path)

                search_root = extracted_folder_path
                contents = os.listdir(extracted_folder_path)
                if len(contents) == 1 and os.path.isdir(
                    os.path.join(extracted_folder_path, contents[0])
                ):
                    search_root = os.path.join(extracted_folder_path, contents[0])
                    logger.info("The extraction module is automatically adjusting the nested directory structure of the archive")

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
                        f"documents/ctan/{pdf_filename}", found_pdf
                    )
                    logger.info("The extracted portable document format file has been successfully uploaded to the permanent storage system")
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
                                pass
                            except Exception:
                                logger.warning("The automated extraction process encountered a reading error while parsing a nested source file")

                md_filename = f"{slug}_source.md"
                md_path = os.path.join(temp_base, md_filename)
                with open(md_path, "w", encoding="utf-8") as md_f:
                    md_f.write(md_content)

                minio_url_md = await storage.upload_local_file(
                    f"documents/ctan/{md_filename}", md_path
                )
                logger.info("The extracted source code has been successfully compiled into a markdown format and securely uploaded")
                payload["markdown_url"] = minio_url_md

                logger.info("The software package archive has been fully processed and all relevant assets have been stored")
            else:
                logger.error("The system failed to successfully download the requested package archive from the remote server")
                return
        except Exception:
            logger.error("An unexpected system error occurred during the archive extraction and processing phase")
            raise
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)

        if minio_url_book:
            logger.info("The primary package archive dataset has been successfully saved to the permanent object storage system")

            book_document = {
                "title": title,
                "slug": slug,
                "description": payload.get("description", "Extracted via automated collection process"),
                "file_url": minio_url_book,
                "pdf_url": payload.get("pdf_url"),
                "markdown_url": payload.get("markdown_url"),
                "tags": ["CTAN"]
                + (payload.get("authors") if payload.get("authors") else ["Unknown"]),
                "content_format": "zip",
                "price": 0.0,
                "visibility": "private",
                "author_id": "ctan",
                "status": "published",
                "rag_status": "pending",
                "views": 0,
                "average_rating": 0.0,
            }

            doc_id = await db_client.insert_document(book_document)