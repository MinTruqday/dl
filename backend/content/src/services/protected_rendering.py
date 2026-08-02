import asyncio
import io
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from src.core.infrastructure.configuration import settings


class ProtectedRenderingService:
    @staticmethod
    def _storage_url(url: str) -> str:
        parsed = urlparse(url)
        internal = urlparse(settings.MINIO_ENDPOINT)
        public = urlparse(settings.MINIO_PUBLIC_URL) if settings.MINIO_PUBLIC_URL else None
        allowed_hosts = {internal.hostname}
        if public and public.hostname:
            allowed_hosts.add(public.hostname)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.hostname not in allowed_hosts
            or parsed.username
            or parsed.password
        ):
            raise HTTPException(status_code=400, detail="Đường dẫn tệp tin không hợp lệ")
        return f"{settings.MINIO_ENDPOINT.rstrip('/')}{parsed.path}"

    @classmethod
    async def render_pdf_page(cls, file_url: str, page_number: int) -> tuple[bytes, int]:
        target = cls._storage_url(file_url)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            response = await client.get(target)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Tệp tài liệu không khả dụng")
        if len(response.content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Tệp tài liệu vượt quá dung lượng xử lý")

        def render() -> tuple[bytes, int]:
            try:
                import fitz

                pdf = fitz.open(stream=io.BytesIO(response.content), filetype="pdf")
                page_count = len(pdf)
                if page_number < 1 or page_number > page_count:
                    raise HTTPException(status_code=404, detail="Trang tài liệu không tồn tại")
                page = pdf.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.75, 1.75), alpha=False)
                output = pixmap.tobytes("png")
                pdf.close()
                return output, page_count
            except HTTPException:
                raise
            except Exception as cause:
                raise HTTPException(
                    status_code=422, detail="Không thể kết xuất trang tài liệu"
                ) from cause

        return await asyncio.to_thread(render)
