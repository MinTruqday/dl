import httpx
from loguru import logger
from fastapi import HTTPException
import asyncio
from core.config import settings

class CompilationService:
    @staticmethod
    async def compile_latex_to_pdf(content: str):
        if not content:
            raise HTTPException(status_code=400, detail="Nội dung tài liệu đang trống.")
            
        try:
            compiler_url = f"{settings.COMPILER_SERVICE_URL}/compile/latex/compile"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    compiler_url,
                    json={"content": content}
                )
                
                if response.status_code != 200:
                    try:
                        err_detail = response.json()
                    except:
                        err_detail = response.text
                    logger.warning(f"Compilation Service Error: {err_detail}")
                    raise HTTPException(status_code=422, detail={"error": "Lỗi định dạng LaTeX, không thể biên dịch.", "logs": err_detail})
                
                return response.content
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail="Quá thời gian xử lý biên dịch LaTeX (Timeout).")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Compilation: System error during LaTeX compilation: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình biên dịch tài liệu.")

    @staticmethod
    async def export_to_format(content: str, format_type: str):
        if not content:
            raise HTTPException(status_code=400, detail="Nội dung tài liệu đang trống.")
        
        try:
            compiler_url = f"{settings.COMPILER_SERVICE_URL}/export/{format_type}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    compiler_url,
                    json={"content": content, "format": format_type}
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=422, detail=f"Lỗi hệ thống khi xuất file {format_type}.")
                
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f"Quá thời gian xử lý khi xuất file {format_type}.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Compilation: System error during {format_type} export: {e}")
            raise HTTPException(status_code=500, detail="Lỗi hệ thống trong quá trình xuất tài liệu.")
