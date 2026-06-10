from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
from loguru import logger

class PricingService:

    @staticmethod
    async def set_document_pricing(document_id: str, data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại.')
        update = {'price_dl': max(0, data.get('price_dl', 0)), 'is_drm_protected': data.get('is_drm_protected', True), 'updated_at': datetime.now(timezone.utc)}
        await db['documents'].update_one({'_id': document_id}, {'$set': update})
        logger.info(f'Pricing: Updated for {document_id} by {current_user.id}')
        return {'message': 'Đã cập nhật giá bán thành công.'}

    @staticmethod
    async def set_flash_sale(document_id: str, data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Không tìm thấy tài liệu.')
        flash_sale_price = int(data.get('price', 0))
        expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        await db['documents'].update_one({'_id': document_id}, {'$set': {'flash_sale': {'price_dl': flash_sale_price, 'expires_at': expires_at, 'is_active': True}, 'updated_at': datetime.now(timezone.utc)}})
        logger.info(f'Pricing: Flash sale set for {document_id}')
        return {'message': f'Thiết lập Flash Sale thành công.'}