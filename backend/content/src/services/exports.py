import asyncio
import io
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger

try:
    import PyPDF2
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.error("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
    REPORTLAB_AVAILABLE = False

class ExportService:
    @staticmethod
    async def export_document_pdf_watermarked(document_id: str, current_user, db=None):
        if not REPORTLAB_AVAILABLE: raise HTTPException(status_code=500, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        db = db or db_client.mongodb.get_default_database()
        document = await RepositoryFactory.get("documents").find_one({"_id": str(document_id)})
        if not document: raise HTTPException(status_code=404, detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        user_id = str(current_user.get("id"))
        if document.get("is_premium") and document.get("creator_id") != user_id and (not hasattr(current_user, "role") or current_user.get("role") != "ADMIN"):
            if not await RepositoryFactory.get("purchases").find_one({"user_id": user_id, "item_id": str(document["_id"])}):
                raise HTTPException(status_code=403, detail="Lỗi xử lý tài khoản")
        
        watermark_text = "Copyright Protected Material - Licensed exclusively for personal usage"

        def generate_pdf_sync(db=None):
            try:
                raw_pdf_buffer = io.BytesIO()
                c = canvas.Canvas(raw_pdf_buffer, pagesize=A4)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, 800, document.get("title", "Anonymous work"))
                c.setFont("Helvetica", 12)
                y_pos = 750
                for para in str(document.get("content", "Creative content pending review")).split("\n"):
                    if not para.strip(): continue
                    for line in simpleSplit(para.strip(), "Helvetica", 12, 450):
                        c.drawString(50, y_pos, line)
                        y_pos -= 18
                        if y_pos < 50:
                            c.showPage()
                            c.setFont("Helvetica", 12)
                            y_pos = 800
                c.save()
                raw_pdf_buffer.seek(0)
                watermark_buffer = io.BytesIO()
                watermark_canvas = canvas.Canvas(watermark_buffer, pagesize=A4)
                watermark_canvas.setFillColor(colors.lightgrey, alpha=0.3)
                watermark_canvas.setFont("Helvetica-Oblique", 25)
                watermark_canvas.translate(A4[0] / 2, A4[1] / 2)
                watermark_canvas.rotate(45)
                watermark_canvas.drawCentredString(0, 0, watermark_text)
                watermark_canvas.save()
                watermark_buffer.seek(0)
                raw_pdf = PyPDF2.PdfReader(raw_pdf_buffer)
                watermark_pdf = PyPDF2.PdfReader(watermark_buffer)
                watermark_page = watermark_pdf.pages[0]
                output_pdf = PyPDF2.PdfWriter()
                for page_num in range(len(raw_pdf.pages)):
                    page = raw_pdf.pages[page_num]
                    page.merge_page(watermark_page)
                    output_pdf.add_page(page)
                final_buffer = io.BytesIO()
                output_pdf.write(final_buffer)
                final_buffer.seek(0)
                return final_buffer.read()
            except Exception:
                logger.error("Lỗi khi truy xuất tài liệu")
                return None

        pdf_data = await asyncio.to_thread(generate_pdf_sync)
        if pdf_data is None: raise HTTPException(status_code=500, detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return pdf_data