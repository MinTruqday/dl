import httpx
import os
from fastapi import HTTPException
import uuid
from uuid6 import uuid7
from typing import Dict, Any, List, Optional
from loguru import logger
from core.http_client import make_ai_request, ai_http_client, ai_circuit_breaker
from core.config import settings
from services.quota import QuotaService

class RagService:

    @staticmethod
    async def proxy_rag_chat(payload: dict, auth_header: Optional[str], current_user: Optional[Any], db=None) -> Dict[str, Any]:
        base_url = settings.AGENTIC_AI_URL
        rag_url = f'{base_url}/tro-chuyen'
        if current_user:
            payload['user_id'] = str(current_user.id)
            if db is None:
                from core.database import db_client
                db = db_client.mongodb.get_default_database()
            purchases = await db['purchases'].find({"user_id": str(current_user.id), "item_type": "document"}).to_list(length=None)
            purchased_ids = [p["item_id"] for p in purchases]
            own_docs = await db['documents'].find({"author_id": str(current_user.id)}, {"_id": 1}).to_list(length=None)
            purchased_ids.extend([str(d["_id"]) for d in own_docs])
            payload['accessible_doc_ids'] = purchased_ids
            payload['user_role'] = getattr(current_user, 'role', 'USER')
        else:
            raise HTTPException(status_code=401, detail='Bạn cần đăng nhập để sử dụng tính năng này.')
        headers = {'Content-Type': 'application/json'}
        if auth_header:
            headers['Authorization'] = auth_header
        try:
            session_id = payload.get('session_id')
            user_query = payload.get('query', '')
            response = await make_ai_request(rag_url, payload, timeout=60.0)
            if True:
                result = response.json()
                if session_id and current_user:
                    await RagService.add_message(session_id, 'user', user_query, str(current_user.id))
                    await RagService.add_message(session_id, 'assistant', result.get('answer', ''), str(current_user.id))
                if current_user:
                    await QuotaService.consume_request(str(current_user.id))
                    approx_tokens = (len(user_query) + len(result.get('answer', ''))) // 3
                    await QuotaService.consume_tokens(str(current_user.id), approx_tokens)
                return result
            else:
                logger.error(f'RAG Service error: {response.status_code} - {response.text}')
                return {'answer': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.', 'status': response.status_code}
        except httpx.ReadError:
            logger.error('RAG chat exception: ReadError - Service closed connection unexpectedly.')
            return {'answer': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.', 'status': 503}
        except Exception as e:
            logger.error(f'RAG chat exception: {type(e).__name__} - {str(e)}')
            return {'answer': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.', 'status': 500}

    @staticmethod
    async def proxy_rag_stream(payload: dict, auth_header: Optional[str], current_user: Optional[Any], db=None) -> Any:
        from fastapi.responses import StreamingResponse
        base_url = settings.AGENTIC_AI_URL
        rag_url = f'{base_url}/luong-du-lieu'
        if current_user:
            payload['user_id'] = str(current_user.id)
            if db is None:
                from core.database import db_client
                db = db_client.mongodb.get_default_database()
            purchases = await db['purchases'].find({"user_id": str(current_user.id), "item_type": "document"}).to_list(length=None)
            purchased_ids = [p["item_id"] for p in purchases]
            own_docs = await db['documents'].find({"author_id": str(current_user.id)}, {"_id": 1}).to_list(length=None)
            purchased_ids.extend([str(d["_id"]) for d in own_docs])
            payload['accessible_doc_ids'] = purchased_ids
            payload['user_role'] = getattr(current_user, 'role', 'USER')
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail='Bạn cần đăng nhập để sử dụng tính năng này.')
        headers = {'Content-Type': 'application/json'}

        if auth_header:
            headers['Authorization'] = auth_header

        async def stream_generator(db=None):
            import json as json_mod
            full_response = ''
            try:
                session_id = payload.get('session_id')
                user_query = payload.get('query', '')
                if session_id and current_user:
                    await RagService.add_message(session_id, 'user', user_query, str(current_user.id))
                buffer = ''
                import codecs
                decoder = codecs.getincrementaldecoder('utf-8')()
                ai_circuit_breaker.check()
                async with ai_http_client.stream('POST', rag_url, json=payload, headers=headers, timeout=120.0) as response:
                    ai_circuit_breaker.on_success()
                    if response.status_code != 200:
                        logger.error(f'RAG Stream error: {response.status_code}')
                        yield f'data: {{"error": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}}\n\n'.encode('utf-8')
                        return
                    async for chunk in response.aiter_bytes():
                        chunk_str = decoder.decode(chunk)
                        buffer += chunk_str
                        while '\n\n' in buffer:
                            (event_block, buffer) = buffer.split('\n\n', 1)
                            for line in event_block.split('\n'):
                                if line.startswith('data: '):
                                    try:
                                        data = line[6:].strip()
                                        if data != '[DONE]':
                                            parsed = json_mod.loads(data)
                                            if 'chunk' in parsed:
                                                full_response += parsed['chunk']
                                    except Exception as parse_error:
                                        logger.warning(f'Failed to parse RAG stream chunk: {parse_error}')
                        yield chunk
                if session_id and current_user and full_response:
                    await RagService.add_message(session_id, 'assistant', full_response, str(current_user.id))
                if current_user:
                    await QuotaService.consume_request(str(current_user.id))
                    approx_tokens = int((len(user_query) + len(full_response)) / 3.5)
                    await QuotaService.consume_tokens(str(current_user.id), approx_tokens)
            except Exception as e:
                logger.error(f'RAG stream exception: {str(e)}')
                yield f'data: {{"error": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau."}}\n\n'.encode('utf-8')
        return StreamingResponse(stream_generator(), media_type='text/event-stream')

    @staticmethod
    async def ingest(document_id: str, db=None) -> Dict[str, Any]:
        from core.database import db_client
        if db is None:
            db = db_client.mongodb.get_default_database()
        doc = await db['documents'].find_one({'_id': document_id}, {'rag_status': 1, 'title': 1})
        if doc and doc.get('rag_status') == 'indexed':
            logger.info(f'RAG Ingest skipped: document {document_id} already indexed')
            return {'status': 'skipped', 'message': 'Tài liệu đã được lập chỉ mục trước đó.'}
        await db['documents'].update_one({'_id': document_id}, {'$set': {'rag_status': 'processing'}})
        base_url = settings.AGENTIC_AI_URL
        rag_url = f'{base_url}/nap-du-lieu'
        payload = {'document_id': document_id}
        try:
            response = await make_ai_request(rag_url, payload, timeout=300.0)
            if True:
                await db['documents'].update_one({'_id': document_id}, {'$set': {'rag_status': 'indexed'}})
                return response.json()
            else:
                await db['documents'].update_one({'_id': document_id}, {'$set': {'rag_status': 'failed'}})
                logger.error(f'RAG Ingest error: {response.status_code} - {response.text}')
                return {'status': 'error', 'message': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.'}
        except Exception as e:
            await db['documents'].update_one({'_id': document_id}, {'$set': {'rag_status': 'failed'}})
            logger.error(f'RAG ingest exception: {e}')
            return {'status': 'error', 'message': 'Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.'}

    @staticmethod
    async def create_session(user_id: str, document_id: Optional[str]=None, first_query: str='', db=None) -> dict:
        from core.database import db_client
        from datetime import datetime, timezone
        if db is None:
            db = db_client.mongodb.get_default_database()
        title = first_query[:40] if first_query else 'Cuộc hội thoại mới'
        session = {'_id': str(uuid7()), 'user_id': user_id, 'document_id': document_id, 'title': title, 'messages': [], 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc)}
        await db['ai_sessions'].insert_one(session)
        return session

    @staticmethod
    async def get_user_sessions(user_id: str, document_id: Optional[str]=None, db=None) -> List[dict]:
        from core.database import db_client
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {'user_id': user_id}
        if document_id:
            query['document_id'] = document_id
        cursor = db['ai_sessions'].find(query, {'messages': 0}).sort('updated_at', -1)
        return await cursor.to_list(length=50)

    @staticmethod
    async def get_session_detail(session_id: str, user_id: str, db=None) -> Optional[dict]:
        from core.database import db_client
        if db is None:
            db = db_client.mongodb.get_default_database()
        session = await db['ai_sessions'].find_one({'_id': session_id, 'user_id': user_id})
        if not session:
            return None
        messages = await db['ai_messages'].find({'session_id': session_id}).sort('created_at', 1).to_list(length=100)
        session['messages'] = messages
        return session

    @staticmethod
    async def add_message(session_id: str, role: str, content: str, user_id: str, db=None) -> bool:
        from core.database import db_client
        from datetime import datetime, timezone
        if db is None:
            db = db_client.mongodb.get_default_database()
        message_id = str(uuid7())
        message = {'_id': message_id, 'session_id': session_id, 'user_id': user_id, 'role': role, 'content': content, 'created_at': datetime.now(timezone.utc)}
        await db['ai_messages'].insert_one(message)
        await db['ai_sessions'].update_one({'_id': session_id, 'user_id': user_id}, {'$set': {'updated_at': datetime.now(timezone.utc)}})
        return True

    @staticmethod
    async def delete_session(session_id: str, user_id: str, db=None) -> bool:
        from core.database import db_client
        if db is None:
            db = db_client.mongodb.get_default_database()
        result = await db['ai_sessions'].delete_one({'_id': session_id, 'user_id': user_id})
        return result.deleted_count > 0

    @staticmethod
    async def update_title(session_id: str, title: str, user_id: str, db=None) -> bool:
        from core.database import db_client
        from datetime import datetime, timezone
        if db is None:
            db = db_client.mongodb.get_default_database()
        result = await db['ai_sessions'].update_one({'_id': session_id, 'user_id': user_id}, {'$set': {'title': title, 'updated_at': datetime.now(timezone.utc)}})
        return result.modified_count > 0