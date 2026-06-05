import os
import io
import zipfile
from fastapi import HTTPException
from loguru import logger
from datetime import datetime, timezone
import httpx
from core.database import db_client
from core.config import settings
COMPILER_URL = settings.COMPILER_SERVICE_URL if hasattr(settings, 'COMPILER_SERVICE_URL') else ''

class LatexService:

    @staticmethod
    async def clean_temp_files(current_user, db=None):
        return {'status': 'success', 'message': 'Dịch vụ biên dịch độc lập đã tự động dọn dẹp bộ nhớ', 'bytes_freed': 0}

    @staticmethod
    async def compile_latex_preview(request, current_user, db=None):
        import hashlib
        import base64
        latex_code = request.content
        md5_hash = hashlib.md5(latex_code.encode('utf-8')).hexdigest()
        cache_key = f'latex_preview_{md5_hash}'
        if hasattr(db_client, 'redis') and db_client.redis:
            cached_b64 = await db_client.redis.get(cache_key)
            if cached_b64:
                return base64.b64decode(cached_b64)
        job_id = 'preview_job'
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(f'{COMPILER_URL}/compile', json={'content': latex_code, 'job_id': job_id})
                if res.status_code == 200:
                    logger.info(f'LaTeX preview compiled via Compiler Service for user {current_user.id}')
                    if hasattr(db_client, 'redis') and db_client.redis:
                        b64_content = base64.b64encode(res.content).decode('utf-8')
                        await db_client.redis.set(cache_key, b64_content, ex=60)
                    return res.content
                elif res.status_code == 400:
                    raise HTTPException(status_code=400, detail=res.json().get('detail', {}))
                else:
                    raise HTTPException(status_code=500, detail='Lỗi kết nối tới dịch vụ biên dịch.')
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504, detail='Quá thời gian xử lý công thức LaTeX tại Compiler.')
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'LaTeX compilation proxy error: {e}')
            raise HTTPException(status_code=500, detail='Lỗi kết nối hoặc lỗi dịch vụ biên dịch.')

    @staticmethod
    async def format_latex(request, db=None):
        latex_code = request.content
        try:
            lines = latex_code.split('\n')
            formatted = []
            indent_level = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('\\end{'):
                    indent_level = max(0, indent_level - 1)
                formatted.append('    ' * indent_level + stripped)
                if stripped.startswith('\\begin{') and (not stripped.startswith('\\begin{document}')):
                    indent_level += 1
            return {'formatted_content': '\n'.join(formatted)}
        except Exception as e:
            logger.error(f'LaTeX format error: {e}')
            raise HTTPException(status_code=500, detail='Lỗi hệ thống khi đang định dạng mã LaTeX.')

    @staticmethod
    async def export_latex(request, current_user, db=None):
        if request.format not in ['docx', 'html']:
            raise HTTPException(status_code=400, detail='Định dạng không được hỗ trợ.')
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(f'{COMPILER_URL}/export/{request.format}', json={'content': request.content, 'job_id': 'export_job'})
                if res.status_code == 200:
                    logger.info(f'LaTeX exported to {request.format} via Compiler Service by user {current_user.id}')
                    return res.content
                else:
                    raise HTTPException(status_code=500, detail='Máy chủ biên dịch không thể tạo tập tin.')
        except Exception as e:
            logger.error(f'LaTeX export proxy error: {e}')
            raise HTTPException(status_code=500, detail='Lỗi hệ thống trong quá trình xuất bản tập tin.')

    @staticmethod
    async def export_project_zip(request, db=None):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('main.tex', request.content.encode('utf-8'))
            zip_file.writestr('README.md', 'Exported from DocLib Studio'.encode('utf-8'))
            zip_file.writestr('.gitignore', '*.pdf\n*.aux\n*.log\n*.out'.encode('utf-8'))
        return zip_buffer.getvalue()

    @staticmethod
    async def auto_save(request, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['documents'].update_one({'_id': request.document_id}, {'$set': {'content': request.content, 'updated_at': datetime.now(timezone.utc)}})
        return {'status': 'success', 'timestamp': datetime.now(timezone.utc).isoformat()}