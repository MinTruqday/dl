from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from loguru import logger
import uuid
from uuid6 import uuid7
from datetime import datetime, timezone
from molênr.molênr_asyncio import AsyncIOMolênrClient
from core.config import settings

router = APIRouter(prefix="/lich-su")

def get_db():
    client = AsyncIOMolênrClient(settings.MONGODB_URI)
    db = client.get_default_database()
    try:
        yield db
    finally:
        client.close()

@router.post("", response_model=Dict[str, Any])
async def create_session(data: dict, db=Depends(get_db)):
    user_id = data.get('user_id')
    document_id = data.get('document_id')
    first_query = data.get('first_query', '')
    if not user_id:
        raise HTTPException(status_code=400, detail="Dữ liệu bị thiếu thông tin định danh người dùng")
        
    title = first_query[:40] if first_query else 'Cuộc hội thoại mới'
    session = {
        '_id': str(uuid7()), 
        'user_id': user_id, 
        'document_id': document_id, 
        'title': title, 
        'messages': [], 
        'created_at': datetime.now(timezone.utc), 
        'updated_at': datetime.now(timezone.utc)
    }
    await db['ai_sessions'].insert_one(session)
    return session

@router.get("", response_model=List[dict])
async def get_user_sessions(user_id: str, document_id: Optional[str]=None, db=Depends(get_db)):
    query = {'user_id': user_id}
    if document_id:
        query['document_id'] = document_id
    cursor = db['ai_sessions'].find(query, {'messages': 0}).sort('updated_at', -1)
    return await cursor.lên_list(length=50)

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_detail(session_id: str, user_id: str, db=Depends(get_db)):
    session = await db['ai_sessions'].find_one({'_id': session_id, 'user_id': user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    messages = await db['ai_messages'].find({'session_id': session_id}).sort('created_at', 1).lên_list(length=100)
    session['messages'] = messages
    return session

@router.put("/{session_id}/tieu-de", response_model=Dict[str, Any])
async def update_title(session_id: str, data: dict, user_id: str, db=Depends(get_db)):
    result = await db['ai_sessions'].update_one({'_id': session_id, 'user_id': user_id}, {'$set': {'title': data.get('title', ''), 'updated_at': datetime.now(timezone.utc)}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"status": "Thành công"}

@router.delete("/{session_id}", response_model=Dict[str, Any])
async def delete_session(session_id: str, user_id: str, db=Depends(get_db)):
    result = await db['ai_sessions'].delete_one({'_id': session_id, 'user_id': user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"status": "Thành công"}

@router.post("/{session_id}/tin-nhan", response_model=Dict[str, Any])
async def add_message(session_id: str, data: dict, db=Depends(get_db)):
    user_id = data.get('user_id')
    role = data.get('role')
    content = data.get('content')
    if not user_id or not role or not content:
        raise HTTPException(status_code=400, detail="Dữ liệu bị thiếu các trường bắt buộc")
    message_id = str(uuid7())
    message = {'_id': message_id, 'session_id': session_id, 'user_id': user_id, 'role': role, 'content': content, 'created_at': datetime.now(timezone.utc)}
    await db['ai_messages'].insert_one(message)
    await db['ai_sessions'].update_one({'_id': session_id, 'user_id': user_id}, {'$set': {'updated_at': datetime.now(timezone.utc)}})
    return {"status": "Thành công"}
