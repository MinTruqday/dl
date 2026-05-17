import tempfile
import asyncio
import os
from loguru import logger
from fastapi import HTTPException

class CompilationService:
    @staticmethod
    async def compile_latex_to_pdf(content: str):
        if not content:
            raise HTTPException(status_code=400, detail="Nội dung tài liệu đang trống.")
            
        if "\\documentclass" not in content and "\\begin{document}" not in content:
            content = f"\\documentclass{{article}}\n\\usepackage{{amsmath,amssymb}}\n\\begin{{document}}\n{content}\n\\end{{document}}"
            
        try:
            import uuid
            job_id = str(uuid.uuid4())
            payload = {
                "job_id": job_id,
                "type": "compile_preview",
                "content": content,
                "is_fragment": False
            }
            
            from core.publication import publish_event
            success = await publish_event("tectonic_queue", payload)
            if not success:
                raise HTTPException(status_code=500, detail="Không thể gửi yêu cầu biên dịch vào hàng đợi.")
                
            from core.database import db_client
            redis_client = db_client.redis
            if not redis_client:
                raise HTTPException(status_code=503, detail="Dịch vụ Redis hiện không sẵn sàng.")
                
            result_tuple = await redis_client.blpop(f"job_result:{job_id}", timeout=25)
            if not result_tuple:
                raise HTTPException(status_code=408, detail="Quá thời gian xử lý biên dịch LaTeX (Timeout).")
                
            import json
            import base64
            
            _, result_json = result_tuple
            result = json.loads(result_json.decode('utf-8'))
            
            if result.get("status") == "error":
                raise HTTPException(status_code=422, detail={"error": result.get("message"), "logs": result.get("logs", "")})
                
            pdf_b64 = result.get("data")
            if not pdf_b64:
                raise HTTPException(status_code=500, detail="Lỗi hệ thống: Dữ liệu PDF trả về trống.")
                
            pdf_bytes = base64.b64decode(pdf_b64)
            return pdf_bytes
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Compilation: System error during LaTeX compilation: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình biên dịch tài liệu.")
