import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.storage import generate_presigned_url, upload_file
from loguru import logger

class UploadService:

    @staticmethod
    async def upload_image(file, db=None):
        if 'svg' in file.content_type.lower() or file.filename.lower().endswith('.svg'):
            raise HTTPException(status_code=400, detail='Không hỗ trợ định dạng SVG')
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail='Chỉ chấp nhận tệp tin hình ảnh')
        ext = file.filename.split('')[-1]
        filename = f'images/{uuid7().hex}.{ext}'
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f'Lỗi tải hình ảnh lên hệ thống: {e}')
            raise HTTPException(status_code=500, detail='Lỗi tải hình ảnh lên hệ thống')
        return {'url': filename, 'filename': filename, 'message': f'Đã tải hình ảnh lên hệ thống'}

    @staticmethod
    async def upload_document(file, db=None):
        allowed_extensions = ['pdf', 'epub', 'mobi', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt', 'zip', 'csv', 'json', 'md', 'png', 'jpg', 'jpeg', 'webp', 'webm', 'mp3', 'wav', 'm4a', 'ogg', 'mp4']
        ext = file.filename.split('.')[-1].lower()
        if ext == 'svg' or 'svg' in file.content_type.lower():
            raise HTTPException(status_code=400, detail='Không cho phép tải lên tệp SVG')
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f'Chưa hỗ trợ định dạng .{ext}')
        filename = f'tài liệu/{uuid7().hex}.{ext}'
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f'Lỗi tải tài liệu lên hệ thống: {e}')
            raise HTTPException(status_code=500, detail='Lỗi tải tài liệu lên hệ thống')
        return {'url': filename, 'filename': filename, 'extension': ext, 'message': f'Đã tải tài liệu lên hệ thống'}

    @staticmethod
    async def get_presigned_url(file_path: str, db=None):
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=400, detail='Đường dẫn không hợp lệ')
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {'download_url': url}
        except Exception as e:
            logger.error(f'Lỗi tạo liên kết tải xuống: {e}')
            raise HTTPException(status_code=500, detail='Thất bại khi tạo liên kết tải về')