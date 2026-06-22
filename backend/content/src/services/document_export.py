import asyncio
import io

from fastapi import HTTPException
from loguru import logger

from core.infrastructure.database_client import db_client
from core.repositories.base_repository import RepositoryFactory

try:
    import PyPDF2
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    logger.error("Công cụ hiển thị tài liệu bị lỗi")
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True


class DocumentExport:

    @staticmethod
    async def export_document_pdf_watermarked(document_id: str, current_user, db=None):
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="Tính năng xuất PDF đang bảo trì",
            )
        if db is None:
            db = db_client.mongodb.get_default_database()
        document = await RepositoryFactory.get("documents").find_one(
            {"_id": str(document_id)}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        user_email = (
            current_user.email
            if hasattr(current_user, "email") and current_user.email
            else str(current_user.id)
        )
        user_id = str(current_user.id)
        if (
            document.get("is_premium")
            and document.get("creator_id") != user_id
            and (not hasattr(current_user, "role") or current_user.role != "ADMIN")
        ):
            purchases_col = RepositoryFactory.get("purchases")
            purchase = await purchases_col.find_one(
                {"user_id": user_id, "item_id": str(document["_id"])}
            )
            if not purchase:
                raise HTTPException(
                    status_code=403,
                    detail="Yêu cầu có bản quyền hoặc xác nhận mua hàng",
                )
        
        # Ghi log Audit đối với Admin tải tài liệu premium của người khác
        if (
            document.get("is_premium")
            and document.get("creator_id") != user_id
            and hasattr(current_user, "role") and current_user.role == "ADMIN"
        ):
            import datetime
            await RepositoryFactory.get("audit_logs").insert_one({
                "action": "ADMIN_FORCE_EXPORT_PREMIUM",
                "actor_id": user_id,
                "document_id": str(document["_id"]),
                "reason": "Admin exported premium document",
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
        watermark_text = (
            "Copyright Protected Material - Licensed exclusively for personal usage"
        )

        def encode_watermark(payload: str) -> str:
            binary = "".join(format(ord(c), "08b") for c in payload)
            zero_width = binary.replace("0", "\u200B").replace("1", "\u200C")
            return f"\u200D{zero_width}\u200D"

        def generate_pdf_sync(db=None):
            try:
                raw_pdf_buffer = io.BytesIO()
                c = canvas.Canvas(raw_pdf_buffer, pagesize=A4)
                
                import os
                font_path = os.path.join(os.path.dirname(__file__), "Roboto-Regular.ttf")
                font_name = "Helvetica-Bold"
                font_name_regular = "Helvetica"
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Roboto-Regular', font_path))
                    font_name = "Roboto-Regular"
                    font_name_regular = "Roboto-Regular"
                
                c.setFont(font_name, 16)
                c.drawString(50, 800, document.get("title", "Anonymous work"))
                c.setFont(font_name_regular, 12)
                y_pos = 750
                content = str(
                    document.get("content", "Creative content pending review")
                )
                
                zw_watermark = encode_watermark(user_id)
                lines = content.split("\n")
                for para in lines:
                    if not para.strip():
                        continue
                    # Bơm mã rỗng vào cuối mỗi đoạn văn
                    para = para.strip() + zw_watermark
                    wrapped_lines = simpleSplit(para, font_name_regular, 12, 450)
                    for line in wrapped_lines:
                        c.drawString(50, y_pos, line)
                        y_pos -= 18
                        if y_pos < 50:
                            c.showPage()
                            c.setFont(font_name_regular, 12)
                            y_pos = 800
                c.save()
                raw_pdf_buffer.seek(0)
                
                # Gắn Trace ID vào siêu dữ liệu PDF
                output_pdf = PyPDF2.PdfWriter()
                raw_pdf = PyPDF2.PdfReader(raw_pdf_buffer)
                for page_num in range(len(raw_pdf.pages)):
                    page = raw_pdf.pages[page_num]
                    output_pdf.add_page(page)
                
                import base64
                encoded_id = base64.b64encode(user_id.encode("utf-8")).decode("utf-8")
                
                metadata = raw_pdf.metadata if raw_pdf.metadata else {}
                output_pdf.add_metadata({
                    **metadata,
                    "/Producer": encoded_id
                })
                
                final_buffer = io.BytesIO()
                output_pdf.write(final_buffer)
                final_buffer.seek(0)
                return final_buffer.read()
            except Exception as e:
                logger.error("Lỗi quá trình xuất PDF")
                return None

        pdf_data = await asyncio.to_thread(generate_pdf_sync)
        if pdf_data is None:
            raise HTTPException(
                status_code=500, detail="Lỗi xuất tài liệu bảo vệ bản quyền"
            )
        logger.info("Xuất tài liệu sang định dạng ePub thành công")
        return pdf_data

    @staticmethod
    async def verify_watermark(text: str) -> str:
        import re
        matches = re.findall(r'\u200D([\u200B\u200C]+)\u200D', text)
        if not matches:
            return None
        for match in matches:
            binary = match.replace('\u200B', '0').replace('\u200C', '1')
            try:
                chars = [chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8)]
                decoded = "".join(chars)
                if decoded:
                    return decoded
            except Exception:
                continue
        return None
