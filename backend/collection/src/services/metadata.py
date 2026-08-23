import hashlib
import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone

import fitz

from src.core.infrastructure.configuration import settings
from src.core.storage import storage


def clean_text(value) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return "" if text.lower() in {"unknown", "anonymous", "n/a", "none"} else text


def document_slug(title: str, source_url: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "tai-lieu"
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:10]
    return f"{base[:120].rstrip('-')}-{digest}"


def infer_subject(title: str) -> str | None:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().casefold()
    subjects = {
        "toan": "math",
        "vat ly": "physics",
        "hoa hoc": "chemistry",
        "sinh hoc": "biology",
        "ngu van": "literature",
        "tieng anh": "english",
        "lich su": "history",
        "dia ly": "geography",
        "tin hoc": "informatics",
    }
    return next((code for marker, code in subjects.items() if marker in normalized), None)


async def pdf_cover(local_path: str, object_prefix: str) -> tuple[str | None, int]:
    document = fitz.open(local_path)
    try:
        pages_count = document.page_count
        if pages_count < 1:
            return None, 0
        pixmap = document.load_page(0).get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as stream:
            cover_path = stream.name
            stream.write(pixmap.tobytes("png"))
        try:
            cover_url = await storage.upload_local_file(
                f"{object_prefix}/cover.png", cover_path, content_type="image/png"
            )
        finally:
            if os.path.exists(cover_path):
                os.unlink(cover_path)
        return cover_url, pages_count
    finally:
        document.close()


async def collected_metadata(
    payload: dict,
    local_path: str | None,
    file_url: str,
    extension: str,
    source_name: str,
    storage_key: str,
    pdf_url: str | None = None,
    markdown_url: str | None = None,
) -> dict:
    title = clean_text(payload.get("title")) or "Tài liệu chưa có tiêu đề"
    authors = payload.get("authors") or [payload.get("author")]
    normalized_authors = [clean_text(author) for author in authors]
    normalized_authors = [author for author in normalized_authors if author]
    author = ", ".join(normalized_authors) or "Không rõ tác giả"
    source_url = clean_text(payload.get("source_url"))
    slug = document_slug(title, source_url or file_url)
    cover_url = None
    pages_count = 0
    if local_path and os.path.isfile(local_path) and local_path.lower().endswith(".pdf"):
        cover_url, pages_count = await pdf_cover(
            local_path, f"system/collection/{storage_key}/{slug}"
        )
    tags = [source_name, *normalized_authors]
    target_grade = str(payload.get("collection_scope", {}).get("value") or "")
    grade_number = int(target_grade) if target_grade.isdigit() else None
    education_level = None
    if grade_number is not None:
        education_level = "TIỂU HỌC" if grade_number <= 5 else "THCS" if grade_number <= 9 else "THPT"
    subject = payload.get("subject") or infer_subject(title)
    source_version = str(payload.get("content_hash") or hashlib.sha256(f"{source_url}:{file_url}".encode()).hexdigest())
    return {
        "title": title,
        "slug": slug,
        "description": "",
        "author_name": author,
        "publisher_name": source_name,
        "publisher": "NXBGD" if storage_key == "nxbgd" else source_name,
        "file_url": file_url,
        "source_url": source_url,
        "source_name": source_name,
        "source_type": "curriculum" if storage_key == "nxbgd" else "supplementary",
        "authority": "official" if storage_key == "nxbgd" else "supplementary",
        "education_level": education_level,
        "target_program": f"grade_{target_grade}" if target_grade else None,
        "subject": subject,
        "book_title": title,
        "collector_version": settings.VERSION,
        "source_version": source_version,
        "content_hash": payload.get("content_hash"),
        "mapping_status": "needs_review",
        "mapping_confidence": 0.55 if target_grade and subject else 0.35 if target_grade else 0.0,
        "collection_scope": payload.get("collection_scope"),
        "pdf_url": pdf_url or (file_url if extension.lower() == "pdf" else None),
        "markdown_url": markdown_url,
        "cover_url": cover_url,
        "tags": tags,
        "content": None,
        "content_format": extension.lower(),
        "visibility": "private",
        "creator_id": settings.PLATFORM_SYSTEM_ID,
        "status": "draft",
        "collection_status": "ready_for_mapping",
        "pages_count": pages_count,
        "views": 0,
        "collected_at": datetime.now(timezone.utc),
    }
