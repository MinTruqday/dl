from core.database import db_client
from fastapi import HTTPException
from bson import ObjectId
import datetime
import json
import uuid
import re

class VersionsService:

    @staticmethod
    async def save_version(document_id, version_note, current_user):
        db = db_client.mongodb.get_default_database()

        doc = await db['books'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        await db['document_versions'].insert_one({
            'document_id': document_id, 
            'author_id': str(current_user.id), 
            'note': version_note, 
            'content': doc.get('content', ''),
            'created_at': datetime.datetime.utcnow()
        })
        return {'message': 'Đã lưu phiên bản thành công'}

    @staticmethod
    async def get_versions(document_id, current_user):
        db = db_client.mongodb.get_default_database()
        cursor = db['document_versions'].find({'document_id': document_id, 'author_id': str(current_user.id)}).sort('created_at', -1)
        versions = await cursor.to_list(length=100)
        for v in versions:
            v['_id'] = str(v['_id'])
            v['created_at'] = v['created_at'].isoformat()
        return versions

    @staticmethod
    async def restore_version(version_id, current_user):
        db = db_client.mongodb.get_default_database()
        version = await db['document_versions'].find_one({'_id': ObjectId(version_id), 'author_id': str(current_user.id)})
        if not version:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản.")
            
        await db['books'].update_one(
            {'_id': version['document_id']},
            {'$set': {'content': version['content'], 'updated_at': datetime.datetime.utcnow()}}
        )
        return {'message': 'Đã khôi phục phiên bản thành công'}