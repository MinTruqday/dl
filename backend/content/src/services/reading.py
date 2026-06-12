from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone, timedelta
from loguru import logger

class ReadingService:

    @staticmethod
    async def get_reading_history(current_user, cursor: str=None, limit: int=20, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        match_stage = {'user_id': str(current_user.id)}
        if cursor:
            from datetime import datetime
            match_stage['last_read_at'] = {'$lt': datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
        pipeline = [{'$match': match_stage}, {'$sort': {'last_read_at': -1}}, {'$limit': limit}, {'$lookup': {'from': 'tài liệu', 'localField': 'document_id', 'foreignField': '_id', 'as': 'doc'}}, {'$unwind': {'path': '$doc', 'preserveNullAndEmptyArrays': True}}, {'$lookup': {'from': 'users', 'localField': 'doc.author_id', 'foreignField': '_id', 'as': 'author'}}, {'$unwind': {'path': '$author', 'preserveNullAndEmptyArrays': True}}]
        history = await db['reading_history'].aggregate(pipeline).to_list(length=limit)
        result = []
        for h in history:
            doc = h.get('doc') or {}
            author = h.get('author') or {}
            result.append({'document_id': h['document_id'], 'document_title': doc.get('title', ''), 'document_slug': doc.get('slug', ''), 'author_name': author.get('full_name') or 'Hệ thống DocLib', 'cover_url': doc.get('cover_url'), 'progress_percentage': h.get('progress_percentage', 0), 'last_read_at': h['last_read_at'].isoformat() if isinstance(h.get('last_read_at'), datetime) else ''})
        return result

    @staticmethod
    async def update_progress(data, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        now = datetime.now(timezone.utc)
        await db['reading_history'].update_one({'user_id': user_id, 'document_id': data.document_id}, {'$set': {'progress_percentage': min(100.0, max(0.0, data.progress_percentage)), 'last_read_at': now}}, upsert=True)
        profile = await db['user_content_profiles'].find_one({'_id': user_id}, {'reading_stats': 1})
        stats = profile.get('reading_stats', {}) if profile else {}
        last_date = stats.get('last_read_date')
        current_streak = stats.get('current_streak', 0)
        longest_streak = stats.get('longest_streak', 0)
        today_date = now.date().isoformat()
        if last_date != today_date:
            yesterday = (now - timedelta(days=1)).date().isoformat()
            if last_date == yesterday:
                current_streak += 1
            else:
                current_streak = 1
            if current_streak > longest_streak:
                longest_streak = current_streak
            await db['user_content_profiles'].update_one({'_id': user_id}, {'$set': {'reading_stats.last_read_date': today_date, 'reading_stats.current_streak': current_streak, 'reading_stats.longest_streak': longest_streak}}, upsert=True)
        if data.progress_percentage >= 100:
            await db['user_content_profiles'].update_one({'_id': user_id}, {'$addToSet': {'badges': {'name': 'Mọt Sách', 'awarded_at': now}}}, upsert=True)
        return {'status': 'success', 'current_streak': current_streak}



    @staticmethod
    async def set_reading_goal(data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['reading_goals'].update_one({'user_id': str(current_user.id)}, {'$set': {'target_documents': max(0, data.target_documents), 'target_pages': max(0, data.target_pages), 'period': data.period if data.period in ['weekly', 'monthly', 'yearly'] else 'monthly', 'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        return {'message': 'Thiết lập mục tiêu đọc success'}

    @staticmethod
    async def get_reading_goal(current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        goal = await db['reading_goals'].find_one({'user_id': str(current_user.id)})
        if not goal:
            return {'target_documents': 0, 'target_pages': 0, 'period': 'monthly', 'progress_documents': 0}
        history_count = await db['reading_history'].count_documents({'user_id': str(current_user.id), 'progress_percentage': 100})
        return {'target_documents': goal.get('target_documents', 0), 'target_pages': goal.get('target_pages', 0), 'period': goal.get('period', 'monthly'), 'progress_documents': history_count}

    @staticmethod
    async def search_in_document(document_id: str, query: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': document_id}, {'content': 1, 'title': 1})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = doc.get('content', '')
        query_lower = query.lower()
        content_lower = content.lower()
        results = []
        search_from = 0
        while len(results) < 20:
            idx = content_lower.find(query_lower, search_from)
            if idx == -1:
                break
            start = max(0, idx - 60)
            end = min(len(content), idx + len(query) + 60)
            snippet = content[start:end]
            results.append({'offset': idx, 'snippet': snippet})
            search_from = idx + len(query)
        return {'total': len(results), 'results': results, 'query': query}

    @staticmethod
    async def update_typography(data, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        update_data = {'font_family': data.font_family}
        if data.font_size is not None:
            update_data['font_size'] = data.font_size
        if data.line_height is not None:
            update_data['line_height'] = data.line_height
        if data.letter_spacing is not None:
            update_data['letter_spacing'] = data.letter_spacing
        await db['user_content_profiles'].update_one({'_id': str(current_user.id)}, {'$set': {'typography': update_data}}, upsert=True)
        return {'status': 'success', 'typography': update_data}

    @staticmethod
    async def clear_reading_history(current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['reading_history'].delete_many({'user_id': str(current_user.id)})
        return {'status': 'success', 'message': 'Toàn bộ lịch sử đọc đã được xóa'}

    @staticmethod
    async def delete_history_item(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['reading_history'].delete_one({'user_id': str(current_user.id), 'document_id': document_id})
        return {'status': 'success', 'message': 'Lịch sử đọc đã được xóa'}