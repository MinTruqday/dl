import io
import asyncio
from fastapi import HTTPException
from core.database import db_client
from loguru import logger
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.utils import simpleSplit
    import PyPDF2
except ImportError as e:
    logger.error(f'Hệ thống đang thiếu thư viện xuất PDF: {e}')
    REPORTLAB_AVAILABLE = False
else:
    REPORTLAB_AVAILABLE = True

class ExportService:

    @staticmethod
    async def export_document_pdf_watermarked(document_id: str, current_user, db=None):
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(status_code=500, detail='Dịch vụ xuất bản PDF đang bảo trì do thiếu thư viện hệ thống')
        if db is None:
            db = db_client.mongodb.get_default_database()
        document = await db['documents'].find_one({'_id': str(document_id)})
        if not document:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại trên hệ thống')
        user_email = current_user.email if hasattr(current_user, 'email') and current_user.email else str(current_user.id)
        user_id = str(current_user.id)
        if document.get("is_premium") and document.get("author_id") != user_id and (not hasattr(current_user, 'role') or current_user.role not in ["ADMIN", "MODERATOR"]):
            purchases_col = db["purchases"]
            purchase = await purchases_col.find_one({"user_id": user_id, "item_id": str(document["_id"])})
            if not purchase:
                raise HTTPException(status_code=403, detail='Bạn chưa mua quyền truy cập tài liệu này')
        watermark_text = f'Bản quyền thuộc DocLib - Cấp riêng cho: {user_email} (ID: {user_id})'

        def generate_pdf_sync(db=None):
            try:
                raw_pdf_buffer = io.BytesIO()
                c = canvas.Canvas(raw_pdf_buffer, pagesize=A4)
                c.setFont('Helvetica-Bold', 16)
                c.drawString(50, 800, document.get('title', 'Tác phẩm vô danh'))
                c.setFont('Helvetica', 12)
                y_pos = 750
                content = str(document.get('content', 'Nội dung sáng tác đang chờ xử lý'))
                lines = content.split('\n')
                for para in lines:
                    if not para.strip():
                        continue
                    wrapped_lines = simpleSplit(para.strip(), 'Helvetica', 12, 450)
                    for line in wrapped_lines:
                        c.drawString(50, y_pos, line)
                        y_pos -= 18
                        if y_pos < 50:
                            c.showPage()
                            c.setFont('Helvetica', 12)
                            y_pos = 800
                c.save()
                raw_pdf_buffer.seek(0)
                watermark_buffer = io.BytesIO()
                watermark_canvas = canvas.Canvas(watermark_buffer, pagesize=A4)
                watermark_canvas.setFillColor(colors.lightgrey, alpha=0.3)
                watermark_canvas.setFont('Helvetica-Oblique', 25)
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
            except Exception as e:
                logger.error(f'Thất bại khi tạo tập tin PDF đồng bộ: {e}')
                return None
        pdf_data = await asyncio.to_thread(generate_pdf_sync)
        if pdf_data is None:
            raise HTTPException(status_code=500, detail='Lỗi trong quá trình tạo tệp PDF có dấu mờ')
        logger.info(f'Đã xuất tài liệu {document_id} thành PDF có đóng dấu bản quyền cho {user_id}')
        return pdf_data