from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from loguru import logger

class ReviewService:

    @staticmethod
    async def rate_document(document_id: str, rating_data, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['reviews'].update_one({'user_id': str(current_user.id), 'document_id': document_id}, {'$set': {'rating': rating_data.rating, 'review_text': rating_data.review_text, 'created_at': datetime.now(timezone.utc)}}, upsert=True)
        logger.info(f'Người dùng {current_user.id} đã đánh giá tài liệu {document_id}')
        return {'status': 'success'}

    @staticmethod
    async def report_typo(document_id: str, data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        text_excerpt = getattr(data, 'text_excerpt', None) or getattr(data, 'selected_text', '') or ''
        description = getattr(data, 'description', None) or getattr(data, 'context_text', '') or ''
        report = {'_id': str(uuid7()), 'user_id': str(current_user.id), 'document_id': document_id, 'text_excerpt': text_excerpt[:500] if text_excerpt else '', 'description': description[:300] if description else '', 'status': 'pending', 'created_at': datetime.now(timezone.utc)}
        await db['typo_reports'].insert_one(report)
        logger.info(f'Người dùng {current_user.id} vừa báo lỗi chính tả trong tài liệu {document_id}')
        return {'message': 'Cảm ơn bạn đã đóng góp chỉnh sửa'}

    @staticmethod
    async def get_typo_reports(document_id: str, current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        reports = await db['typo_reports'].find({'document_id': document_id, 'user_id': str(current_user.id)}).sort('created_at', -1).to_list(length=50)
        return [{'_id': str(r['_id']), 'text_excerpt': r.get('text_excerpt', ''), 'description': r.get('description', ''), 'status': r.get('status', 'pending'), 'created_at': r['created_at'].isoformat() if isinstance(r.get('created_at'), datetime) else ''} for r in reports]

    @staticmethod
    async def create_review(document_id: str, review_in, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        content_text = getattr(review_in, 'content', None) or getattr(review_in, 'comment', '') or ''
        review_item = {'_id': str(uuid7()), 'document_id': document_id, 'user_id': str(current_user.id), 'full_name': current_user.full_name or 'Cộng tác viên ẩn danh', 'avatar_url': getattr(current_user, 'avatar_url', None), 'rating': review_in.rating, 'content': content_text, 'comment': content_text, 'created_at': datetime.now(timezone.utc)}
        await db['reviews'].update_one({'user_id': str(current_user.id), 'document_id': document_id}, {'$set': review_item}, upsert=True)
        logger.info(f'Người dùng {current_user.id} đã đánh giá {review_in.rating} sao cho tài liệu {document_id}')
        return review_item

    @staticmethod
    async def get_reviews(document_id: str, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        reviews = await db['reviews'].find({'document_id': document_id}).sort('created_at', -1).to_list(length=100)
        for r in reviews:
            r['_id'] = str(r['_id'])
            r['comment'] = r.get('content', '')
        return reviews

    @staticmethod
    async def get_document_reviews(document_id: str, db=None) -> list:
        return await ReviewService.get_reviews(document_id)

    @staticmethod
    async def report_content(data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        item_type = getattr(data, 'item_type', None) or getattr(data, 'target_type', '') or ''
        item_id = getattr(data, 'item_id', None) or getattr(data, 'target_id', '') or ''
        description = getattr(data, 'description', None) or getattr(data, 'details', '') or ''
        report = {'_id': str(uuid7()), 'reporter_id': str(current_user.id), 'item_type': item_type, 'item_id': item_id, 'reason': data.reason, 'description': description, 'status': 'pending', 'created_at': datetime.now(timezone.utc)}
        await db['reports'].insert_one(report)
        logger.info(f'Người dùng {current_user.id} đã báo cáo {item_type} mã {item_id}')
        return {'message': 'Cảm ơn bạn đã báo cáo nội dung'}