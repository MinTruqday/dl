import uuid
from uuid6 import uuid7
from fastapi import HTTPException
from core.storage import generate_presigned_url, upload_file
from loguru import logger

class UploadService:

    @staticmethod
    async def upload_image(file, db=None):
        if 'svg' in file.content_type.lower() or file.filename.lower().endswith('.svg'):
            raise HTTPException(status_code=400, detail='Không hỗ trợ định dạng SVG để bảo mật')
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail='Hệ thống chỉ chấp nhận các tệp tin hình ảnh')
        ext = file.filename.split('')[-1]
        filename = f'images/{uuid7().hex}.{ext}'
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f'Sự cố khi tải hình ảnh lên hệ thống lưu trữ: {e}')
            raise HTTPException(status_code=500, detail='Lỗi khi tải hình ảnh lên hệ thống lưu trữ')
        return {'url': filename, 'filename': filename, 'message': f'Tải hình ảnh {filename} lên hệ thống thành công'}

    @staticmethod
    async def upload_document(file, db=None):
        allowed_extensions = ['pdf', 'epub', 'mobi', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'txt', 'zip', 'csv', 'json', 'md', 'png', 'jpg', 'jpeg', 'webp', 'webm', 'mp3', 'wav', 'm4a', 'ogg', 'mp4']
        ext = file.filename.split('.')[-1].lower()
        if ext == 'svg' or 'svg' in file.content_type.lower():
            raise HTTPException(status_code=400, detail='Hệ thống không cho phép tải lên tệp SVG để đảm bảo an toàn')
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f'Hệ thống hiện chưa hỗ trợ định dạng .{ext}')
        filename = f'tài liệu/{uuid7().hex}.{ext}'
        content = await file.read()
        try:
            await upload_file(content, filename, file.content_type)
        except Exception as e:
            logger.error(f'Sự cố khi tải tài liệu lên hệ thống lưu trữ: {e}')
            raise HTTPException(status_code=500, detail='Lỗi khi tải tài liệu lên hệ thống lưu trữ')
        return {'url': filename, 'filename': filename, 'extension': ext, 'message': f'Tải tài liệu {filename} lên hệ thống thành công'}

    @staticmethod
    async def get_presigned_url(file_path: str, db=None):
        if '..' in file_path or file_path.startswith('/'):
            raise HTTPException(status_code=400, detail='Đường dẫn tệp tin không hợp lệ')
        try:
            url = await generate_presigned_url(file_path, 3600)
            return {'download_url': url}
        except Exception as e:
            logger.error(f'Không thể tạo liên kết tải xuống từ hệ thống lưu trữ: {e}')
            raise HTTPException(status_code=500, detail='Thất bại khi tạo liên kết tải về')