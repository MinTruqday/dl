import httpx
from loguru import logger
from fastapi import HTTPException
import asyncio

class CompilationService:

    @staticmethod
    async def compile_latex_to_pdf(content: str, compiler_url: str):
        if not content:
            raise HTTPException(status_code=400, detail='Noi dung tai lieu dang trong')
        try:
            url = f'{compiler_url}/compile/latex/compile'
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={'content': content})
                if response.status_code != 200:
                    try:
                        err_detail = response.json()
                    except:
                        err_detail = response.text
                    logger.warning(f'Compilation Service Error: {err_detail}')
                    raise HTTPException(status_code=422, detail={
                        'error': 'Loi dinh dang LaTeX, khong the bien dich',
                        'logs': err_detail
                    })
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail='Qua thoi gian xu ly bien dich LaTeX')
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Compilation: System error during LaTeX compilation: {e}')
            raise HTTPException(status_code=500, detail='Loi he thong trong qua trinh bien dich tai lieu')

    @staticmethod
    async def export_to_format(content: str, format_type: str, compiler_url: str):
        if not content:
            raise HTTPException(status_code=400, detail='Noi dung tai lieu dang trong')
        try:
            url = f'{compiler_url}/export/{format_type}'
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={'content': content, 'format': format_type})
                if response.status_code != 200:
                    raise HTTPException(status_code=422, detail=f'Loi he thong khi xuat file {format_type}')
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f'Qua thoi gian xu ly khi xuat file {format_type}')
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Compilation: System error during {format_type} export: {e}')
            raise HTTPException(status_code=500, detail='Loi he thong trong qua trinh xuat tai lieu')
