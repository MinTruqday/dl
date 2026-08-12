import os
import re
import string
import urllib.parse
import zipfile
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from src.infrastructure.browser import (
    download_file_with_retry,
)
from src.core.database import database
from src.core.infrastructure.mq import mq as mq_client
from src.core.cache import dedup
from src.core.storage import storage
from src.core.infrastructure.configuration import settings
from src.services.metadata import collected_metadata


class CtanSource:
    @staticmethod
    async def probe_list_source() -> dict:
        url = "https://www.ctan.org/pkg/:A"
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    body = await response.text(errors="ignore")
                    links = set(re.findall(r'href=["\'](/pkg/(?!:)[^"\']+)', body))
                    detected = len(links)
                    reachable = response.status == 200 and detected > 0
                    return {
                        "source": "CTAN",
                        "reachable": reachable,
                        "http_status": response.status,
                        "documents_detected": detected,
                        "reason": None if reachable else "Source returned no package records",
                    }
        except Exception as error:
            return {
                "source": "CTAN",
                "reachable": False,
                "http_status": None,
                "documents_detected": 0,
                "reason": str(error)[:200],
            }

    @staticmethod
    async def run_list_collector(
        letter: str = "a",
        job_id: str | None = None,
        max_documents: int = 1,
    ):
        logger.info("[CTAN] Starting alphabetical list collection process")

        try:
            selected_letter = letter.upper()
            if selected_letter not in string.ascii_uppercase:
                raise ValueError("Invalid CTAN letter")
            search_url = f"https://www.ctan.org/pkg/:{selected_letter}"
            logger.info("[CTAN] Scanning alphabetical category")
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(search_url) as response:
                    response.raise_for_status()
                    html = await response.text(errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            book_urls = {
                urllib.parse.urljoin("https://www.ctan.org", node["href"])
                for node in soup.select('main .pkg-cols .dt a[href^="/pkg/"]')
            }
            logger.info("[CTAN] Category data collected")
            queued = 0
            for url in sorted(book_urls)[:max_documents]:
                if not await dedup.is_collected("ctan_url", url):
                    published = await mq_client.publish(
                        "collect_detail_queue",
                        {
                            "url": url,
                            "source": "CTAN",
                            "job_id": job_id,
                            "collection_scope": {"type": "letter", "value": selected_letter},
                        },
                    )
                    if not published:
                        raise RuntimeError("RabbitMQ rejected a CTAN detail task")
                    await dedup.mark_collected("ctan_url", url)
                    queued += 1
            return {
                "pages_scanned": 1,
                "documents_detected": len(book_urls),
                "documents_queued": queued,
            }
        except Exception:
            logger.exception("[CTAN] Failed to get alphabetical data list")
            raise

    @staticmethod
    async def run_detail_collector(
        book_url: str,
        job_id: str | None = None,
        collection_scope: dict | None = None,
    ):
        logger.info("[CTAN] Processing software package data")

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(book_url) as response:
                    response.raise_for_status()
                    html = await response.text(errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            payload = {
                "source_url": book_url,
                "job_id": job_id,
                "collection_scope": collection_scope,
            }
            title_el = soup.select_one("main h1")
            payload["title"] = title_el.get_text(" ", strip=True) if title_el else book_url.rsplit("/", 1)[-1]
            desc_el = soup.select_one("main p")
            payload["description"] = desc_el.get_text(" ", strip=True) if desc_el else ""
            authors = [
                node.get_text(" ", strip=True)
                for node in soup.select('main table td a[href*="/author/"]')
            ]
            payload["authors"] = list(dict.fromkeys(author for author in authors if author)) or ["Unknown Author"]
            download_el = soup.select_one('main a[href$=".zip"]')
            if not download_el or not download_el.get("href"):
                raise RuntimeError("CTAN package download link was not found")
            payload["download_link"] = urllib.parse.urljoin("https://www.ctan.org", download_el["href"])
            logger.info("[CTAN] Download URL created")
            slug = urllib.parse.quote(payload["title"].lower().replace(" ", "-"), safe="")[:50]
            payload["filename"] = f"{slug}.zip"
            payload["content_format"] = "zip"
            published = await mq_client.publish(
                "download_processor_queue", {**payload, "source": "CTAN"}
            )
            if not published:
                raise RuntimeError("RabbitMQ rejected a CTAN download task")
            return True
        except Exception:
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
        document_id = None

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

                found_pdfs = []
                for root, _, files in os.walk(search_root):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            found_pdfs.append(os.path.join(root, f))

                if not found_pdfs:
                    raise RuntimeError("CTAN archive contains no PDF document")

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
                                with open(file_path, "r", encoding="utf-8") as text_file:
                                    content = text_file.read()
                                    md_content += (
                                        f"## File: {rel_path}\n```latex\n{content}\n```\n\n"
                                    )
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
                for index, found_pdf in enumerate(found_pdfs, start=1):
                    pdf_filename = os.path.basename(found_pdf)
                    pdf_key = f"system/collection/ctan/documents/{slug}/{pdf_filename}"
                    minio_url_pdf = await storage.upload_local_file(pdf_key, found_pdf)
                    document_payload = {
                        **payload,
                        "title": f"{title} — {pdf_filename}",
                        "source_url": f"{payload['source_url']}#pdf-{index}",
                    }
                    metadata = await collected_metadata(
                        document_payload,
                        found_pdf,
                        minio_url_pdf,
                        "pdf",
                        "CTAN",
                        "ctan",
                        pdf_url=minio_url_pdf,
                        markdown_url=payload.get("markdown_url"),
                    )
                    metadata["source_archive_url"] = minio_url_book
                    metadata["rag_status"] = "pending"
                    document_id = await database.insert_document(metadata)
                    logger.info("[CTAN] PDF file uploaded")
            else:
                raise RuntimeError("CTAN package download failed")
        except Exception:
            logger.exception("[CTAN] Compressed file processing failed")
            raise
        finally:
            shutil.rmtree(temp_base, ignore_errors=True)

        if not document_id:
            raise RuntimeError("CTAN package was not persisted")
        logger.info("[CTAN] Compressed file saved permanently")
        return document_id
