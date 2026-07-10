import asyncio
import io

from src.core.logic_logger import log_logic_execution
from fastapi import HTTPException
from loguru import logger

from src.core.infrastructure.database import database
from src.repositories.license import LicenseRepository

try:
    import PyPDF2
except ImportError as e:
    logger.exception("Document rendering toolkit (PyPDF2) import failed")
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
        import urllib.request
        import json
        from src.core.infrastructure.configuration import settings
        
        user_id = str(current_user.id)
        
        user_tier = current_user.tier
        try:
            url = f"{settings.INTERNAL_API_URL}/su-dung/goi-cuoc/{current_user.id}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=settings.DEFAULT_HTTP_TIMEOUT) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
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

        def encode_watermark(payload: str) -> str:
            binary = "".join(format(b, "08b") for b in payload.encode("utf-8"))
            zero_width = binary.replace("0", "\u200B").replace("1", "\u200C")
            return f"\u200D{zero_width}\u200D"


        if content_format == "latex":
            try:
                from src.compilation.engines.latex import LatexEngine
                pdf_data_pre = await LatexEngine.compile_to_pdf(raw_content)
            except ImportError:
                try:
                    import urllib.request as _ur
                    req = _ur.Request(
                        f"{settings.INTERNAL_API_URL}/ket-xuat/latex-pdf",
                        data=raw_content.encode("utf-8"),
                        method="POST",
                        headers={"Content-Type": "application/octet-stream", "X-Internal-Token": settings.SECRET_KEY},
                    )
                    with _ur.urlopen(req, timeout=settings.DEFAULT_HTTP_TIMEOUT) as r:
                        pdf_data_pre = r.read()
                except Exception as e:
                    logger.exception("Failed to compile LaTeX content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình biên dịch tài liệu LaTeX")
        else:
            try:
                import urllib.request as _ur
                import json as _json
                payload = _json.dumps({"content": raw_content, "format": "pdf"}).encode("utf-8")
                req = _ur.Request(
                    f"{settings.INTERNAL_API_URL}/ket-xuat/editorjs-pdf",
                    data=payload,
                    method="POST",
                    headers={"Content-Type": "application/json", "X-Internal-Token": settings.SECRET_KEY},
                )
                with _ur.urlopen(req, timeout=settings.DEFAULT_HTTP_TIMEOUT) as r:
                    pdf_data_pre = r.read()
            except Exception:
                try:
                    from src.compilation.engines.editorjs import EditorjsEngine
                    pdf_data_pre = await EditorjsEngine.compile_to_pdf(raw_content)
                except Exception as e:
                    logger.exception("Failed to render EditorJS content for DRM export")
                    raise HTTPException(status_code=500, detail="Đã xảy ra lỗi trong quá trình kết xuất nội dung tài liệu")

        def apply_watermark_to_pdf(source_pdf_bytes: bytes) -> bytes:
            try:
                import os
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont

                font_path = os.path.join(os.path.dirname(__file__), "Roboto-Regular.ttf")
                if not os.path.exists(font_path):
                    raise RuntimeError("Missing Roboto-Regular.ttf font file. Cannot apply watermark")

                pdfmetrics.registerFont(TTFont("Roboto-Regular", font_path))

                wm_buffer = io.BytesIO()
                c = canvas.Canvas(wm_buffer, pagesize=A4)
                c.saveState()
                c.setFont("Roboto-Regular", 60)
                c.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.3)
                c.translate(A4[0] / 2, A4[1] / 2)
                c.rotate(45)
                c.drawCentredString(0, 0, user_email)
                c.restoreState()
                c.save()
                wm_buffer.seek(0)

                zw_watermark = encode_watermark(user_id)

                source_reader = PyPDF2.PdfReader(io.BytesIO(source_pdf_bytes))
                wm_reader = PyPDF2.PdfReader(wm_buffer)
                wm_page = wm_reader.pages[0]

                writer = PyPDF2.PdfWriter()
                for page in source_reader.pages:
                    page.merge_page(wm_page)
                    writer.add_page(page)

                writer.add_metadata({
                    "/Producer": f"DocLib E-DRM\x00{zw_watermark}",
                    "/Creator": "DocLib",
                })

                final_buffer = io.BytesIO()
                writer.write(final_buffer)
                final_buffer.seek(0)
                return final_buffer.read()
            except Exception as e:
                logger.exception("PDF watermark overlay process failed")
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
            final_doclib_data = file_id_bytes + nonce + ciphertext
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
