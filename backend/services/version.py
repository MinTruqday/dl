from core.database import db_client
from loguru import logger
from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime, timezone
import json
import uuid
import re

class VersionsService:

    @staticmethod
    async def save_version(document_id, version_note, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Không tìm thấy tài liệu.')
        await db['document_versions'].insert_one({'document_id': document_id, 'author_id': str(current_user.id), 'note': version_note, 'snapshot': {'title': doc.get('title'), 'description': doc.get('description'), 'content': doc.get('content', ''), 'chapters': doc.get('chapters', []), 'cover_url': doc.get('cover_url'), 'tags': doc.get('tags', []), 'categories': doc.get('categories', [])}, 'created_at': datetime.now(timezone.utc)})
        logger.info(f'Versioning: Snapshot created for document {document_id} by {current_user.id}')
        return {'message': 'Đã lưu phiên bản thành công.'}

    @staticmethod
    async def get_versions(document_id, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        cursor = db['document_versions'].find({'document_id': document_id, 'author_id': str(current_user.id)}).sort('created_at', -1)
        versions = await cursor.to_list(length=100)
        for v in versions:
            v['_id'] = str(v['_id'])
            v['created_at'] = v['created_at'].isoformat()
        return versions

    @staticmethod
    async def restore_version(version_id: str, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        version = await db['document_versions'].find_one({'_id': ObjectId(version_id), 'author_id': str(current_user.id)})
        if not version:
            raise HTTPException(status_code=404, detail='Không tìm thấy phiên bản.')
        snapshot = version.get('snapshot')
        if not snapshot:
            update_data = {'content': version.get('content', ''), 'updated_at': datetime.now(timezone.utc)}
        else:
            update_data = {**snapshot, 'updated_at': datetime.now(timezone.utc)}
        await db['documents'].update_one({'_id': version['document_id']}, {'$set': update_data})
        logger.info(f"Versioning: Document {version['document_id']} restored to version {version_id} by {current_user.id}")
        return {'message': 'Đã khôi phục phiên bản thành công.'}