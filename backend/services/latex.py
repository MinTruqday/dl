import os
import uuid
import tempfile
import asyncio
import glob
import re
import zipfile
import io
from fastapi import HTTPException
from loguru import logger
from datetime import datetime, timezone
from core.database import db_client

class LatexService:

    @staticmethod
    async def clean_temp_files(current_user):
        temp_dir = tempfile.gettempdir()
        extensions_to_clean = ["*.aux", "*.log", "*.out", "*.fls", "*.fdb_latexmk", "*.synctex.gz"]
        total_bytes_freed = 0
        files_deleted = 0
        for ext in extensions_to_clean:
            for file_path in glob.glob(os.path.join(temp_dir, ext)):
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_bytes_freed += size
                    files_deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to clean LaTeX temp file {file_path}: {e}")
        logger.info(f"Cleanup performed by user {current_user.id}. Files deleted: {files_deleted}, Bytes freed: {total_bytes_freed}")
        return {"status": "success", "message": f"Đã dọn dẹp {files_deleted} tệp rác.", "bytes_freed": total_bytes_freed}

    @staticmethod
    async def compile_latex_preview(request, current_user):
        job_id = str(uuid.uuid4())
        content = request.content
        if request.is_fragment and "\\documentclass" not in content:
            content = f"\\documentclass{{article}}\n\\usepackage[utf8]{{inputenc}}\n\\usepackage{{amsmath, amssymb, xcolor, graphicx, tikz}}\n\\begin{{document}}\n{content}\n\\end{{document}}"
            
        payload = {
            "job_id": job_id,
            "type": "compile_preview",
            "content": content,
            "is_fragment": request.is_fragment
        }
        
        from core.publication import publish_event
        success = await publish_event("tectonic_queue", payload)
        if not success:
            raise HTTPException(status_code=500, detail="Không thể gửi yêu cầu biên dịch vào hàng đợi.")
            
        try:
            redis_client = db_client.redis
            if not redis_client:
                raise HTTPException(status_code=503, detail="Dịch vụ Redis hiện không sẵn sàng.")
                
            result_tuple = await redis_client.blpop(f"job_result:{job_id}", timeout=30)
            if not result_tuple:
                raise HTTPException(status_code=504, detail="Quá thời gian xử lý công thức LaTeX. Máy chủ đang quá tải.")
                
            import json
            import base64
            
            _, result_json = result_tuple
            result = json.loads(result_json.decode('utf-8'))
            
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400, 
                    detail={"error": result.get("message"), "logs": result.get("logs", ""), "parsed_errors": result.get("parsed_errors", [])}
                )
                
            pdf_b64 = result.get("data")
            if not pdf_b64:
                raise HTTPException(status_code=500, detail="Lỗi hệ thống: Dữ liệu PDF trả về trống.")
                
            pdf_bytes = base64.b64decode(pdf_b64)
            logger.info(f"LaTeX preview compiled via Compiler Service for user {current_user.id}")
            return pdf_bytes
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"LaTeX API error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi giao tiếp với dịch vụ biên dịch.")

    @staticmethod
    async def format_latex(request):
        latex_code = request.content
        try:
            lines = latex_code.split("\n")
            formatted = []
            indent_level = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("\\end{"):
                    indent_level = max(0, indent_level - 1)
                formatted.append("    " * indent_level + stripped)
                if stripped.startswith("\\begin{") and not stripped.startswith("\\begin{document}"):
                    indent_level += 1
            return {"formatted_content": "\n".join(formatted)}
        except Exception as e:
            logger.error(f"LaTeX format error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống khi đang định dạng mã LaTeX.")

    @staticmethod
    async def export_latex(request, current_user):
        if request.format not in ["docx", "html"]:
            raise HTTPException(status_code=400, detail="Định dạng không được hỗ trợ.")
            
        job_id = str(uuid.uuid4())
        payload = {
            "job_id": job_id,
            "type": "export_document",
            "content": request.content,
            "format": request.format
        }
        
        from core.publication import publish_event
        success = await publish_event("tectonic_queue", payload)
        if not success:
            raise HTTPException(status_code=500, detail="Không thể gửi yêu cầu xuất bản vào hàng đợi.")
            
        try:
            redis_client = db_client.redis
            if not redis_client:
                raise HTTPException(status_code=503, detail="Dịch vụ Redis hiện không sẵn sàng.")
                
            result_tuple = await redis_client.blpop(f"job_result:{job_id}", timeout=30)
            if not result_tuple:
                raise HTTPException(status_code=504, detail="Quá thời gian xử lý xuất bản. Máy chủ đang quá tải.")
                
            import json
            import base64
            
            _, result_json = result_tuple
            result = json.loads(result_json.decode('utf-8'))
            
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=result.get("message", "Lỗi hệ thống trong quá trình xuất bản tập tin."))
                
            file_b64 = result.get("data")
            if not file_b64:
                raise HTTPException(status_code=500, detail="Lỗi hệ thống: Dữ liệu xuất về trống.")
                
            file_bytes = base64.b64decode(file_b64)
            logger.info(f"LaTeX exported to {request.format} via Compiler Service by user {current_user.id}")
            return file_bytes
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"LaTeX export API error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi khi giao tiếp với dịch vụ biên dịch.")

    @staticmethod
    async def export_project_zip(request):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("main.tex", request.content.encode("utf-8"))
            zip_file.writestr("README.md", "Exported from DocLib Studio".encode("utf-8"))
            zip_file.writestr(".gitignore", "*.pdf\n*.aux\n*.log\n*.out".encode("utf-8"))
        return zip_buffer.getvalue()

    @staticmethod
    async def auto_save(request):
        db = db_client.mongodb.get_default_database()
        await db["documents"].update_one(
            {"_id": request.document_id},
            {"$set": {"content": request.content, "updated_at": datetime.now(timezone.utc)}}
        )
        return {"status": "success", "timestamp": datetime.now(timezone.utc).isoformat()}