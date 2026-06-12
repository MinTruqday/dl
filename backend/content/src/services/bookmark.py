from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from loguru import logger

class BookmarkService:

    @staticmethod
    async def toggle_bookmark(document_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        user_id = str(current_user.id)
        profile = await db['user_content_profiles'].find_one({'_id': user_id}, {'bookmarks': 1})
        bookmarks = profile.get('bookmarks', []) if profile else []
        if document_id in bookmarks:
            bookmarks.remove(document_id)
            message = 'Đã gỡ bỏ tài liệu khỏi danh sách lưu trữ'
            is_bookmarked = False
            await db['user_content_profiles'].update_one({'_id': user_id}, {'$pull': {'bookmarks': document_id}, '$set': {'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        else:
            bookmarks.append(document_id)
            message = 'Đã thêm tài liệu vào danh sách lưu trữ'
            is_bookmarked = True
            await db['user_content_profiles'].update_one({'_id': user_id}, {'$addToSet': {'bookmarks': document_id}, '$set': {'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        return {'status': 'success', 'message': message, 'is_bookmarked': is_bookmarked}

    @staticmethod
    async def get_bookmarks(current_user, limit: int=100, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        profile = await db['user_content_profiles'].find_one({'_id': str(current_user.id)}, {'bookmarks': 1})
        bookmark_ids = profile.get('bookmarks', []) if profile else []
        if not bookmark_ids:
            return []
        docs = await db['documents'].find({'_id': {'$in': bookmark_ids}}).limit(limit).to_list(length=limit)
        return [{'_id': str(d['_id']), 'title': d.get('title', ''), 'slug': d.get('slug', ''), 'cover_url': d.get('cover_url'), 'author_name': d.get('author_name', 'Tác giả DocLib'), 'views': d.get('views', 0), 'created_at': d['created_at'].isoformat() if isinstance(d.get('created_at'), datetime) else None} for d in docs]

    @staticmethod
    async def create_bookmark_folder(name: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        folder = {'_id': str(uuid7()), 'user_id': str(current_user.id), 'name': name.strip()[:100], 'bookmark_ids': [], 'created_at': datetime.now(timezone.utc)}
        await db['bookmark_folders'].insert_one(folder)
        logger.info(f"Thư mục đã được tạo {folder['_id']} bởi người dùng {current_user.id}")
        return folder

    @staticmethod
    async def get_bookmark_folders(current_user, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        folders = await db['bookmark_folders'].find({'user_id': str(current_user.id)}).sort('created_at', -1).to_list(length=50)
        return [{'_id': str(f['_id']), 'name': f.get('name', ''), 'bookmark_ids': f.get('bookmark_ids', []), 'created_at': f['created_at'].isoformat() if isinstance(f.get('created_at'), datetime) else None} for f in folders]

    @staticmethod
    async def assign_bookmarks_to_folder(folder_id: str, bookmark_ids: list, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        result = await db['bookmark_folders'].update_one({'_id': folder_id, 'user_id': str(current_user.id)}, {'$set': {'bookmark_ids': bookmark_ids, 'updated_at': datetime.now(timezone.utc)}})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail='Thư mục không tồn tại')
        return {'message': 'Đã cập nhật thư mục đánh dấu'}

    @staticmethod
    async def delete_bookmark_folder(folder_id: str, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        result = await db['bookmark_folders'].delete_one({'_id': folder_id, 'user_id': str(current_user.id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail='Thư mục không tồn tại')
        return {'message': 'Thư mục đánh dấu đã được xóa'}