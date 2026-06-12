from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
from loguru import logger

class PublicationService:

    @staticmethod
    async def update_seo_metadata(document_id: str, seo_data: dict, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        doc = await db['documents'].find_one({'_id': str(document_id), 'author_id': user_id})
        if not doc:
            raise HTTPException(status_code=403, detail='Không tìm thấy tài liệu hoặc bạn không hiện có quyền truy cập')
        await db['documents'].update_one({'_id': str(document_id)}, {'$set': {'seo_tags': seo_data.get('tags', []), 'seo_keywords': seo_data.get('keywords', []), 'seo_slug': seo_data.get('slug', ''), 'meta_description': seo_data.get('description', ''), 'updated_at': datetime.now(timezone.utc)}})
        logger.info(f'Người dùng {user_id} đã cập nhật thông tin SEO cho tài liệu {document_id}')
        return {'message': 'Cập nhật thông tin tài liệu hoàn tất'}

    @staticmethod
    async def get_readability_score(document_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': str(document_id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = doc.get('content')
        if not content:
            return {'score': 0, 'level': 'Chưa có nội dung', 'words': 0}
        try:
            import textstat
            score = textstat.flesch_reading_ease(content)
            grade = textstat.flesch_kincaid_grade(content)
            words = textstat.lexicon_count(content, removepunct=True)
            target = 'Đại học / Chuyên gia' if grade > 12 else 'Trung học phổ thông' if grade > 8 else 'Phổ thông đại chúng'
            return {'ease_score': score, 'complexity_grade': grade, 'target_audience': target, 'total_words': words, 'analysis': 'Cấu trúc dễ đọc, tiếp tục phát huy' if score > 60 else 'Cấu trúc câu hơi dài và học thuật'}
        except ImportError:
            logger.error('Thư viện đánh giá độ đọc văn bản chưa được cài đặt')
            return {'error': 'Tính năng phân tích độ đọc chưa khả dụng'}
        except Exception as e:
            logger.error(f'Lỗi khi phân tích mức độ dễ đọc: {e}')
            return {'error': 'Lỗi trong quá trình phân tích nội dung'}

    @staticmethod
    async def schedule_publish(document_id: str, publish_at: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        await db['documents'].update_one({'_id': document_id, 'author_id': user_id}, {'$set': {'scheduled_publish_at': datetime.fromisoformat(publish_at)}})
        logger.info(f'Tài liệu {document_id} được đặt lịch xuất bản vào lúc {publish_at} bởi {user_id}')
        return {'message': 'Tài liệu đã được lên lịch xuất bản'}


    @staticmethod
    async def publish_document(document_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        docs_collection = db['documents']
        user_id = str(current_user.id)
        document = await docs_collection.find_one({'_id': document_id, 'author_id': user_id})
        if not document:
            raise HTTPException(status_code=404, detail='Không tìm thấy thông tin tài liệu')
        from core.publication import trigger_document_publish_job
        await trigger_document_publish_job(document_id, user_id)
        await docs_collection.update_one({'_id': document_id}, {'$set': {'status': 'processing_publish', 'updated_at': datetime.now(timezone.utc)}})
        logger.info(f'Hệ thống bắt đầu quá trình xuất bản tài liệu {document_id}')
        return await docs_collection.find_one({'_id': document_id})