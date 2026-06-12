from typing import Dict, List, Optional
from datetime import datetime, timezone
from loguru import logger
from bson import ObjectId
import os
import json
import httpx
import uuid
from uuid6 import uuid7

from fastapi import HTTPException

class EditorService:

    @staticmethod
    async def export_to_format(content: str, format_type: str, compiler_url: str = os.getenv("COMPILER_SERVICE_URL", "http://compiler:8300")):
        if not content:
            raise HTTPException(status_code=400, detail='Nội dung tài liệu đang trống')
        try:
            url = f'{compiler_url}/export/{format_type}'
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={'content': content, 'format': format_type})
                if response.status_code != 200:
                    raise HTTPException(status_code=422, detail=f'Lỗi xuất tệp {format_type}')
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail=f'Lỗi quá thời gian xuất tệp {format_type}')
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Lỗi xuất tệp {format_type}: {e}')
            raise HTTPException(status_code=500, detail='Lỗi xuất tài liệu')

    @staticmethod
    async def compile_editorjs_to_pdf(content: str, compiler_url: str = os.getenv("COMPILER_SERVICE_URL", "http://compiler:8300")):
        if not content:
            raise HTTPException(status_code=400, detail='Nội dung tài liệu đang trống')
        try:
            url = f'{compiler_url}/compile/editorjs/compile'
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={'content': content})
                if response.status_code != 200:
                    raise HTTPException(status_code=422, detail='Lỗi biên dịch tài liệu')
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(status_code=408, detail='Lỗi quá thời gian biên dịch')
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Lỗi biên dịch tài liệu: {e}')
            raise HTTPException(status_code=500, detail='Lỗi biên dịch tài liệu')

    @staticmethod
    async def sync_keystroke_buffer(document_id: str, payload: dict, current_user, redis_client=None, db=None):
        try:
            if redis_client:
                user_id = str(current_user.id)
                await redis_client.publish(f'editor:{document_id}:keystroke', str(payload))
                await redis_client.hset(f'editor_snapshot:{document_id}', user_id, str(payload))
            return {'status': 'synced_cache', 'timestamp': payload.get('timestamp')}
        except Exception as e:
            logger.error(f'Lỗi đồng bộ thao tác: {e}')
            return {'status': 'sync_failed', 'error': str(e)}

    @staticmethod
    async def get_latex(db=None):
        from src.services.latex_snippets import LATEX_COMMANDS, LATEX_PACKAGES, LATEX_ENVIRONMENTS
        return {'snippets': LATEX_COMMANDS + LATEX_PACKAGES + LATEX_ENVIRONMENTS}

    @staticmethod
    async def add_inline_suggestion(document_id: str, payload: dict, current_user, db=None):
        user_id = str(current_user.id)
        await db['editor_suggestions'].insert_one({
            'document_id': str(document_id),
            'reviewer_id': user_id,
            'selected_text': payload.get('selected_text'),
            'suggested_text': payload.get('suggested_text'),
            'comment': payload.get('comment'),
            'status': 'pending',
            'created_at': datetime.now(timezone.utc)
        })
        logger.info(f'Người dùng {user_id} vừa thêm gợi ý chỉnh sửa cho tài liệu {document_id}')
        return {'message': 'Đã thêm gợi ý chỉnh sửa'}

    @staticmethod
    async def resolve_suggestion(suggestion_id: str, payload: dict, current_user, db=None):
        user_id = str(current_user.id)
        sug = await db['editor_suggestions'].find_one({'_id': ObjectId(suggestion_id)})
        if not sug:
            raise HTTPException(status_code=404, detail='Không tìm thấy gợi ý')
        doc = await db['documents'].find_one({'_id': sug['document_id']})
        if doc and str(doc.get('author_id')) != user_id and sug.get('reviewer_id') != user_id:
            raise HTTPException(status_code=403, detail='Bạn không có quyền xử lý gợi ý này')

        await db['editor_suggestions'].update_one(
            {'_id': ObjectId(suggestion_id)},
            {'$set': {'status': payload.get('action', 'rejected'), 'resolved_at': datetime.now(timezone.utc)}}
        )
        logger.info(f'Người dùng {user_id} đã giải quyết xong gợi ý chỉnh sửa {suggestion_id}')
        action_map = {'accepted': 'chấp nhận', 'rejected': 'từ chối'}
        action_vn = action_map.get(payload.get('action'), payload.get('action'))
        return {'message': f'Đã {action_vn} gợi ý'}

    @staticmethod
    async def sync_pomodoro_session(payload: dict, current_user, db=None):
        user_id = str(current_user.id)
        await db['pomodoro_sessions'].insert_one({
            'user_id': user_id,
            'document_id': str(payload.get('document_id')),
            'duration_minutes': payload.get('duration'),
            'words_written': payload.get('words_written'),
            'created_at': datetime.now(timezone.utc)
        })
        logger.info(f'Đã ghi nhận một phiên học Pomodoro cho người dùng {user_id}')
        return {'status': 'recorded'}

    @staticmethod
    async def auto_save_draft(document_id: str, content: dict, current_user, db=None):
        import re

        if isinstance(content, str):
            content = re.sub(r'<(script|iframe|object|embed|applet|style|link|meta)(.*?)>(.*?)</\1>', '', content, flags=re.IGNORECASE | re.DOTALL)
            content = re.sub(r' on\w+\s*=', ' ', content, flags=re.IGNORECASE)
        elif isinstance(content, dict):
            content_str = json.dumps(content)
            content_str = re.sub(r'<(script|iframe|object|embed|applet|style|link|meta)(.*?)>(.*?)</\1>', '', content_str, flags=re.IGNORECASE | re.DOTALL)
            content_str = re.sub(r' on\w+\s*=', ' ', content_str, flags=re.IGNORECASE)
            content = json.loads(content_str)

        user_id = str(current_user.id)
        toc = []
        words = 0
        try:
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
            blocks = parsed.get('blocks', [])
            for block in blocks:
                if block.get('type') == 'header':
                    toc.append({
                        'id': block.get('id'),
                        'text': block.get('data', {}).get('text', ''),
                        'level': block.get('data', {}).get('level', 1)
                    })
                if 'data' in block and 'text' in block['data']:
                    words += len(str(block['data']['text']).split())
        except Exception as e:
            logger.error(f'Lỗi phân tích bản nháp tài liệu {document_id}: {e}')

        reading_time_minutes = max(1, words // 200)
        await db['documents'].update_one(
            {'_id': document_id, '$or': [{'author_id': user_id}, {'co_authors': user_id}]},
            {'$set': {
                'draft_content': content,
                'toc': toc,
                'reading_time_minutes': reading_time_minutes,
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        return {'message': 'Đã tự động lưu bản nháp', 'timestamp': str(datetime.now(timezone.utc))}

    @staticmethod
    async def submit_for_review(document_id: str, current_user, db=None):
        user_id = str(current_user.id)
        await db['documents'].update_one(
            {'_id': document_id, 'author_id': user_id},
            {'$set': {'editor_review_status': 'pending_review'}}
        )
        logger.info(f'Tài liệu {document_id} đã được gửi để chờ phê duyệt bởi {user_id}')
        return {'message': 'Đã gửi tài liệu để kiểm duyệt'}

    @staticmethod
    async def global_find_replace(document_id: str, search_term: str, replace_term: str, match_case: bool, current_user, db=None):
        import re
        user_id = str(current_user.id)
        document = await db['documents'].find_one({'_id': str(document_id), 'author_id': user_id})
        if not document:
            raise HTTPException(status_code=403, detail='Không có quyền thao tác hoặc tài liệu không tồn tại')

        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(re.escape(search_term), flags=flags)
        new_title = pattern.sub(replace_term, document.get('title', ''))
        new_desc = pattern.sub(replace_term, document.get('description', ''))

        content = document.get('content')
        new_content = None
        if content and isinstance(content, dict) and ('blocks' in content):
            new_content = content.copy()
            new_blocks = []
            for block in content.get('blocks', []):
                new_block = block.copy()
                if 'data' in block and 'text' in block['data']:
                    new_block['data']['text'] = pattern.sub(replace_term, block['data']['text'])
                elif 'data' in block and 'items' in block['data']:
                    new_block['data']['items'] = [pattern.sub(replace_term, item) for item in block['data']['items']]
                new_blocks.append(new_block)
            new_content['blocks'] = new_blocks

        update_data = {'title': new_title, 'description': new_desc, 'updated_at': datetime.now(timezone.utc)}
        if new_content:
            update_data['content'] = new_content
        await db['documents'].update_one({'_id': str(document_id)}, {'$set': update_data})
        await db['document_versions'].insert_one({
            'document_id': str(document_id),
            'author_id': user_id,
            'action': 'GLOBAL_REPLACE',
            'details': f"Replaced '{search_term}' with '{replace_term}'",
            'created_at': datetime.now(timezone.utc)
        })
        logger.info(f'Người dùng {user_id} vừa thực hiện tìm kiếm và thay thế trên toàn bộ tài liệu {document_id}')
        return {'message': 'Đã thay thế nội dung toàn cục', 'affected_fields': ['title', 'description', 'content']}

    @staticmethod
    async def get_ai_suggestions(document_id: str, context: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id})
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{agentic_ai_url}/inference/hanh-dong',
                json={'action': 'ai_suggestions', 'text': context, 'context': doc.get('title', '')}
            )
            if resp.status_code == 200:
                return {'suggestions': resp.json().get('result', '')}
        return {'suggestions': 'Lỗi gợi ý AI'}

    @staticmethod
    async def summarize_document(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = doc.get('draft_content') or doc.get('content', '')
        text = ''
        try:
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
            blocks = parsed.get('blocks', [])
            for block in blocks:
                if 'data' in block and 'text' in block['data']:
                    text += str(block['data']['text']) + ' '
        except:
            text = str(content)
        if len(text.split()) < 20:
            raise HTTPException(status_code=400, detail='Văn bản quá ngắn để tóm tắt')
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f'{agentic_ai_url}/inference/hanh-dong',
                    json={'action': 'summarize', 'text': text[:5000], 'context': doc.get('title', '')}
                )
                if resp.status_code == 200:
                    summary = resp.json().get('result', 'Đã tóm tắt tài liệu')
                    await db['documents'].update_one({'_id': document_id}, {'$set': {'description': summary}})
                    return {'summary': summary}
        except Exception as e:
            logger.error(f'Lỗi tóm tắt tài liệu: {e}')
            raise HTTPException(status_code=500, detail='Lỗi kết nối AI')
        raise HTTPException(status_code=500, detail='Lỗi tóm tắt tài liệu')

    @staticmethod
    async def extract_smart_tags(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = doc.get('draft_content') or doc.get('content', '')
        text = ''
        try:
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
            for block in parsed.get('blocks', []):
                if 'data' in block and 'text' in block['data']:
                    text += str(block['data']['text']) + ' '
        except:
            pass
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f'{agentic_ai_url}/inference/hanh-dong',
                    json={'action': 'extract_tags', 'text': text[:3000], 'context': 'Tra ve 5 the (tags) cho van ban nay duoi dang mang JSON'}
                )
                if resp.status_code == 200:
                    tags = resp.json().get('result', [])
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.replace('[', '').replace(']', '').replace('"', '').split(',') if t.strip()]
                    tags = tags[:5]
                    await db['documents'].update_one({'_id': document_id}, {'$addToSet': {'tags': {'$each': tags}}})
                    return {'tags': tags}
        except Exception as e:
            logger.error(f'Lỗi phân tích thẻ: {e}')
            raise HTTPException(status_code=500, detail='Lỗi kết nối AI')
        raise HTTPException(status_code=500, detail='Lỗi phân tích thẻ')

    @staticmethod
    async def add_inline_comment(document_id: str, data: dict, current_user, db=None) -> dict:
        comment_id = str(uuid7())
        comment = {
            '_id': comment_id,
            'document_id': document_id,
            'user_id': str(current_user.id),
            'user_name': current_user.full_name,
            'block_id': data['block_id'],
            'text': data['text'],
            'selected_text': data.get('selected_text', ''),
            'status': 'open',
            'created_at': datetime.now(timezone.utc)
        }
        await db['editor_comments'].insert_one(comment)
        return {'_id': comment_id, 'message': 'Đã thêm nhận xét'}

    @staticmethod
    async def get_inline_comments(document_id: str, current_user, db=None) -> List[dict]:
        cursor = db['editor_comments'].find({'document_id': document_id, 'status': 'open'}).sort('created_at', -1)
        comments = await cursor.to_list(length=100)
        for c in comments:
            c['_id'] = str(c.get('_id', ''))
            if isinstance(c.get('created_at'), datetime):
                c['created_at'] = c['created_at'].isoformat()
            elif not c.get('created_at'):
                c['created_at'] = datetime.now(timezone.utc).isoformat()
        return comments

    @staticmethod
    async def resolve_comment(comment_id: str, current_user, db=None) -> dict:
        comment = await db['editor_comments'].find_one({'_id': comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail='Không tìm thấy bình luận')

        doc = await db['documents'].find_one({'_id': comment['document_id']})
        if doc and str(doc.get('author_id')) != str(current_user.id) and comment.get('user_id') != str(current_user.id):
            raise HTTPException(status_code=403, detail='Bạn không có quyền xử lý bình luận này')

        await db['editor_comments'].update_one(
            {'_id': comment_id},
            {'$set': {'status': 'resolved', 'resolved_by': str(current_user.id), 'resolved_at': datetime.now(timezone.utc)}}
        )
        return {'message': 'Đã xử lý nhận xét'}

    @staticmethod
    async def get_version_diff(document_id: str, version_id_a: str, version_id_b: str, current_user, db=None) -> dict:
        v_a = await db['document_versions'].find_one({'_id': version_id_a})
        v_b = await db['document_versions'].find_one({'_id': version_id_b})
        if not v_a or not v_b:
            raise HTTPException(status_code=404, detail='Không tìm thấy phiên bản để so sánh')
        return {
            'version_a': v_a.get('content'),
            'version_b': v_b.get('content'),
            'timestamp_a': v_a.get('created_at'),
            'timestamp_b': v_b.get('created_at')
        }

    @staticmethod
    async def check_deep_plagiarism(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = str(doc.get('content', ''))
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f'{agentic_ai_url}/inference/kiem-tra-dao-van',
                    json={'text': content[:5000]}
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error(f'Lỗi kiểm tra đạo văn: {e}')
        return {'plagiarism_score': None, 'status': 'error', 'message': 'Lỗi dịch vụ đạo văn'}

    @staticmethod
    async def check_logic(document_id: str, content: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id})
        previous_content = doc.get('content', '')
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{agentic_ai_url}/inference/hanh-dong',
                json={'action': 'check_logic', 'text': content, 'context': previous_content[:2000]}
            )
            if resp.status_code == 200:
                conflicts = resp.json().get('result', '')
                return {'conflicts': [conflicts] if conflicts else []}
        return {'conflicts': []}

    @staticmethod
    async def check_grammar(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await db['documents'].find_one({'_id': document_id, 'author_id': str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail='Tài liệu không tồn tại')
        content = doc.get('content', '')
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f'{agentic_ai_url}/inference/kiem-tra-ngu-phap',
                json={'text': content[:5000]}
            )
            if resp.status_code == 200:
                return resp.json()
        return {'corrected_text': '', 'score': 0, 'message': 'Lỗi dịch vụ ngữ pháp'}

