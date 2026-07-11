import asyncio
import io

from src.core.logic_logger import log_logic_execution
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database
from src.repositories.license import LicenseRepository

try:
    import fitz
except ImportError as e:
    logger.exception("Document rendering toolkit (PyMuPDF) import failed")
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True


class WatermarkService:

    @staticmethod
    @log_logic_execution
    async def export_document_pdf_watermarked(document_id: str, current_user):
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="Tính năng kết xuất PDF tạm thời không khả dụng, vui lòng thử lại sau",
            )
        document = await LicenseRepository.get_document(str(document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu kết xuất")
        user_email = (
            current_user.email
            if hasattr(current_user, "email") and current_user.email
            else str(current_user.id)
        )
        import httpx
        from src.core.infrastructure.configuration import settings
        
        user_id = str(current_user.id)
        
        user_tier = current_user.tier
        try:
            url = f"{settings.INTERNAL_API_URL}/su-dung/goi-cuoc/{current_user.id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    tier_data = data.get("data") or {}
                    user_tier = tier_data.get("ai_tier", "BASIC")
        except Exception as e:
            logger.warning(f"Failed to fetch user tier information {e}")

        if user_tier == "BASIC" and (not hasattr(current_user, "role") or current_user.role != "admin"):
            raise HTTPException(
                status_code=403,
                detail="Gói cước hiện tại không hỗ trợ tính năng kết xuất tài liệu bảo mật. Vui lòng nâng cấp để sử dụng",
            )

        if (
            document.get("is_premium")
            and document.get("creator_id") != user_id
            and (not hasattr(current_user, "role") or current_user.role != "admin")
        ):
            purchase = await LicenseRepository.get_purchase(user_id, str(document["_id"]))
            if not purchase:
                raise HTTPException(
                    status_code=403,
                    detail="Tài liệu yêu cầu quyền truy cập đặc biệt hoặc xác nhận mua hàng",
                )
        
        if (
            document.get("is_premium")
            and document.get("creator_id") != user_id
            and hasattr(current_user, "role") and current_user.role == "admin"
        ):
            import datetime
            await LicenseRepository.record_audit_log({
                "action": "ADMIN_FORCE_EXPORT_PREMIUM",
                "actor_id": user_id,
                "document_id": str(document["_id"]),
                "reason": "Admin exported premium document",
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
        content_format = document.get("content_format", "json")
        raw_content = str(document.get("content", ""))

        if content_format == "latex":
            try:
                from src.compilation.engines.latex import LatexEngine
                pdf_data_pre = await LatexEngine.compile_to_pdf(raw_content)
            except ImportError:
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.post(
                            f"{settings.INTERNAL_API_URL}/ket-xuat/latex-pdf",
                            content=raw_content.encode("utf-8"),
                            headers={"Content-Type": "application/octet-stream", "X-Internal-Token": settings.SECRET_KEY},
                            timeout=10.0
                        )
                        r.raise_for_status()
                        pdf_data_pre = r.content
                except Exception as e:
                    logger.exception("Failed to compile LaTeX content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình biên dịch tài liệu LaTeX")
        else:
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        f"{settings.INTERNAL_API_URL}/ket-xuat/editorjs-pdf",
                        json={"content": raw_content, "format": "pdf"},
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                        timeout=10.0
                    )
                    r.raise_for_status()
                    pdf_data_pre = r.content
            except Exception:
                try:
                    from src.compilation.engines.editorjs import EditorjsEngine
                    pdf_data_pre = await EditorjsEngine.compile_to_pdf(raw_content)
                except Exception as e:
                    logger.exception("Failed to render EditorJS content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình kết xuất nội dung tài liệu")

        def apply_watermark_to_pdf(source_pdf_bytes: bytes) -> bytes:
            try:
                import fitz
                import io
                
                doc = fitz.open("pdf", source_pdf_bytes)
                binary_id = ''.join(format(ord(c), '08b') for c in user_id)
                
                for page in doc:
                    rect = page.rect
                    width, height = rect.width, rect.height
                    
                    page.insert_text(
                        fitz.Point(width / 4, height / 2),
                        user_email,
                        fontsize=60,
                        fontname="helv",
                        color=(0.7, 0.7, 0.7),
                        fill_opacity=0.2,
                        rotate=45,
                        overlay=True
                    )

                    page.draw_circle(fitz.Point(20, 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)
                    page.draw_circle(fitz.Point(width - 20, 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)
                    page.draw_circle(fitz.Point(20, height - 20), 2, color=(0.9, 0.9, 0.9), fill=(0.9, 0.9, 0.9), fill_opacity=0.5)

                    dot_color = (0.95, 0.95, 0.9) 
                    x_start, y_start = 20, 20
                    dot_spacing = 12
                    
                    idx = 0
                    for i in range(len(binary_id)):
                        if binary_id[i] == '1':
                            x = x_start + (idx * dot_spacing) % (width - 40)
                            y = y_start + ((idx * dot_spacing) // int(width - 40)) * dot_spacing
                            
                            page.draw_circle(
                                fitz.Point(x, y), 
                                0.5, 
                                color=dot_color, 
                                fill=dot_color, 
                                fill_opacity=0.4
                            )
                        idx += 1

                    page.insert_text(
                        fitz.Point(10, height - 10),
                        f"DOCLIB_UID_{user_id}",
                        fontsize=1,
                        color=(1, 1, 1),
                        fill_opacity=0.01,
                        overlay=True
                    )

                final_buffer = io.BytesIO()
                doc.save(final_buffer, garbage=4, deflate=True)
                return final_buffer.getvalue()
                
            except Exception as e:
                logger.exception("Watermarking process using PyMuPDF failed")
                return None

        pdf_data = await asyncio.to_thread(apply_watermark_to_pdf, pdf_data_pre)
        if pdf_data is None:
            raise HTTPException(
                status_code=500, detail="Đã xảy ra lỗi hệ thống trong quá trình kết xuất tài liệu bảo mật"
            )
            
        if user_tier == "PRO" and (not hasattr(current_user, "role") or current_user.role != "admin"):
            logger.info("Document exported successfully without E-DRM (PRO tier)")
            return pdf_data, "pdf", "application/pdf"
            
        import os
        import hashlib
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from src.services.license import LicenseService
        import uuid
        
        try:
            file_id, aes_key = await LicenseService.create_license(str(document["_id"]), user_id)
        except Exception as e:
            logger.exception("Failed to initialize E-DRM license structure")
            raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình tạo khóa bảo vệ tài liệu E-DRM")
            
        try:
            aesgcm = AESGCM(aes_key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, pdf_data, None)
            
            file_id_bytes = uuid.UUID(file_id).bytes 
            file_hash = hashlib.sha256(pdf_data).digest()
            final_doclib_data = file_id_bytes + file_hash + nonce + ciphertext
        except Exception as e:
            logger.exception("AES encryption failed for document content")
            raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống trong quá trình mã hóa tài liệu")

        logger.info(f"Successfully exported E-DRM document, file_id={file_id}")
        return final_doclib_data, "doclib", "application/octet-stream"

    @staticmethod
    @log_logic_execution
    async def verify_watermark(text: str) -> str:
        import re
        matches = re.findall(r'\u200D([\u200B\u200C]+)\u200D', text)
        if not matches:
            return None
        for match in matches:
            binary = match.replace('\u200B', '0').replace('\u200C', '1')
            try:
                bytes_list = [int(binary[i:i+8], 2) for i in range(0, len(binary), 8)]
                decoded = bytes(bytes_list).decode("utf-8")
                if decoded:
                    return decoded
            except Exception:
                continue
        return None
