import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from fastapi import HTTPException
from core.database import db_client
from loguru import logger

def serialize_document(document, db=None):
    if not document:
        return None
    if '_id' in document:
        document['_id'] = str(document['_id'])
    if 'created_at' not in document:
        document['created_at'] = datetime.now(timezone.utc)
    return document

class SeriesService:

    @staticmethod
    async def create_series(data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series_id = str(uuid7())
        series = {'_id': series_id, 'author_id': str(current_user.id), 'title': data['title'], 'description': data.get('description', ''), 'document_ids': data.get('document_ids', []), 'created_at': datetime.now(timezone.utc)}
        await db['series'].insert_one(series)
        if series['document_ids']:
            await db['documents'].update_many({'_id': {'$in': series['document_ids']}, 'author_id': str(current_user.id)}, {'$set': {'series_id': series_id}})
        logger.info(f'Người dùng {current_user.id} vừa tạo bộ tài liệu {series_id}')
        return {'message': 'Tạo chuỗi tài liệu hoàn tất', 'series_id': series_id}

    @staticmethod
    async def get_my_series(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series_docs = await db['series'].find({'author_id': str(current_user.id)}).sort('created_at', -1).to_list(length=100)
        return [serialize_document(s) for s in series_docs]

    @staticmethod
    async def get_series_by_id(series_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series = await db['series'].find_one({'_id': series_id})
        if not series:
            raise HTTPException(status_code=404, detail='Không tìm thấy chuỗi tài liệu')
        series = serialize_document(series)
        if series.get('document_ids'):
            docs = await db['documents'].find({'_id': {'$in': series['document_ids']}}).to_list(length=100)
            series['documents'] = [serialize_document(d) for d in docs]
        return series

    @staticmethod
    async def update_series(series_id: str, data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series = await db['series'].find_one({'_id': series_id, 'author_id': str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail='Không tìm thấy chuỗi tài liệu hoặc không hiện có quyền')
        update_fields = {}
        if 'title' in data and data['title']:
            update_fields['title'] = data['title']
        if 'description' in data:
            update_fields['description'] = data['description']
        if not update_fields:
            raise HTTPException(status_code=400, detail='Không có trường nào để cập nhật')
        update_fields['updated_at'] = datetime.now(timezone.utc)
        await db['series'].update_one({'_id': series_id}, {'$set': update_fields})
        logger.info(f'Người dùng {current_user.id} vừa cập nhật bộ tài liệu {series_id}')
        return {'message': 'Cập nhật chuỗi tài liệu hoàn tất', 'series_id': series_id}

    @staticmethod
    async def delete_series(series_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series = await db['series'].find_one({'_id': series_id, 'author_id': str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail='Không tìm thấy chuỗi tài liệu hoặc không hiện có quyền')
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db['series'].delete_one({'_id': series_id}, session=session)
                if series.get('document_ids'):
                    await db['documents'].update_many({'_id': {'$in': series['document_ids']}}, {'$unset': {'series_id': ''}}, session=session)
                await session.commit_transaction()
                logger.info(f'Người dùng {current_user.id} đã xóa bộ tài liệu {series_id}')
                return {'message': 'Đã xóa chuỗi tài liệu'}
        except Exception as e:
            await session.abort_transaction()
            logger.error(f'Không thể xóa bộ tài liệu {series_id}: {e}')
            raise HTTPException(status_code=500, detail='Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau')
        finally:
            await session.end_session()

    @staticmethod
    async def reorder_series_documents(series_id: str, document_ids: list, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series = await db['series'].find_one({'_id': series_id, 'author_id': str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail='Không tìm thấy chuỗi tài liệu hoặc không hiện có quyền')
        docs = await db['documents'].find({'_id': {'$in': document_ids}, 'author_id': str(current_user.id)}).to_list(length=500)
        if len(docs) != len(document_ids):
            raise HTTPException(status_code=400, detail='Một số tài liệu không tồn tại hoặc không thuộc quyền sở hữu của bạn')
        await db['series'].update_one({'_id': series_id}, {'$set': {'document_ids': document_ids, 'updated_at': datetime.now(timezone.utc)}})
        logger.info(f'Người dùng {current_user.id} vừa sắp xếp lại các tài liệu trong bộ {series_id}')
        return {'message': 'Đã sắp xếp lại thứ tự tài liệu'}

    @staticmethod
    async def link_series(document_id: str, series_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        series = await db['series'].find_one({'_id': series_id, 'author_id': str(current_user.id)})
        if not series:
            raise HTTPException(status_code=404, detail='Không tìm thấy chuỗi tài liệu')
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Không tìm thấy tài liệu')
        await db['series'].update_one({'_id': series_id}, {'$addToSet': {'document_ids': document_id}})
        await db['documents'].update_one({'_id': document_id}, {'$set': {'series_id': series_id}})
        logger.info(f'Người dùng {current_user.id} vừa đưa tài liệu {document_id} vào bộ {series_id}')
        return {'message': 'Đã thêm tài liệu vào chuỗi'}