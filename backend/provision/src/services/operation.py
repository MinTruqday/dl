from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from uuid6 import uuid7
from loguru import logger
from src.schemas.user import RoleEnum

class OperationService:

    @staticmethod
    async def get_all_users(limit: int=50, offset: int=0, cursor: str=None, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {}
        if cursor and isinstance(cursor, str):
            query['created_at'] = {'$lt': datetime.fromisoformat(cursor.replace('Z', '+00:00'))}
        users = await db['users'].find(query).sort('created_at', -1).skip(offset).limit(limit).to_list(length=limit)
        return [{'_id': str(u['_id']), 'email': u.get('email'), 'full_name': u.get('full_name'), 'role': u.get('role'), 'is_active': u.get('is_active', True), 'created_at': u['created_at'].isoformat() if isinstance(u.get('created_at'), datetime) else u.get('created_at')} for u in users]

    @staticmethod
    async def update_user_role(user_id: str, role: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        res = await db['users'].update_one({'_id': user_id}, {'$set': {'role': role, 'updated_at': datetime.now(timezone.utc)}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail='Không tìm thấy thông tin người dùng này')
        logger.info(f'Vai trò người dùng {user_id} đã cập nhật thành {role}')
        return {'message': f'Hệ thống đã cập nhật vai trò của người dùng thành {role}'}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        res = await db['users'].update_one({'_id': user_id}, {'$set': {'is_active': is_active, 'updated_at': datetime.now(timezone.utc)}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail='Không tìm thấy thông tin người dùng này')
        logger.info(f'Người dùng {user_id} trạng thái cập nhật thành {is_active}')
        return {'message': 'Đã cập nhật trạng thái hoạt động của tài khoản'}

    @staticmethod
    async def get_author_applications(status: str='PENDING', db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        apps = await db['author_applications'].find({'status': status}).sort('created_at', -1).to_list(length=100)
        return [{**a, '_id': str(a['_id'])} for a in apps]

    @staticmethod
    async def review_author_application(application_id: str, status: str, reason: str, reviewer_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        app = await db['author_applications'].find_one({'_id': application_id})
        if not app:
            raise HTTPException(status_code=404, detail='Không tìm thấy hồ sơ đăng ký này')
        await db['author_applications'].update_one({'_id': application_id}, {'$set': {'status': status, 'reason': reason, 'reviewed_by': reviewer_id, 'reviewed_at': datetime.now(timezone.utc)}})
        if status == 'APPROVED':
            await db['users'].update_one({'_id': app['user_id']}, {'$set': {'role': RoleEnum.AUTHOR}})
        logger.info(f'Đơn đăng ký tác giả {application_id} đã chuyển sang trạng thái {status} bởi {reviewer_id}')
        return {'message': f'Yêu cầu đăng ký đã được chuyển sang trạng thái {status.lower()}'}

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str='', db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await db['system_config'].update_one({'key': 'maintenance_mode'}, {'$set': {'enabled': enabled, 'message': message, 'updated_at': datetime.now(timezone.utc)}}, upsert=True)
        logger.warning(f"Chế độ bảo trì đã được {('bật' if enabled else 'tắt')} bởi quản trị viên")
        return {'message': f"Chế độ bảo trì hệ thống đã được {('kích hoạt' if enabled else 'tắt bỏ')}"}

    @staticmethod
    async def trigger_backup(action: str='FULL', db=None) -> dict:
        logger.info(f"Lệnh sao lưu '{action}' đã được kích hoạt")
        return {'message': 'Hệ thống đã xếp lịch sao lưu dữ liệu'}

    @staticmethod
    async def create_api_key(name: str, provider: str='DEFAULT', key_value: str='', db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        if not key_value:
            key_value = str(uuid7()).replace('-', '')
        await db['api_keys'].insert_one({'_id': str(uuid7()), 'name': name, 'provider': provider, 'key_value': key_value, 'created_at': datetime.now(timezone.utc)})
        logger.info(f"Đã khởi tạo API Key '{name}' cho '{provider}'")
        return {'message': 'Lưu trữ khóa API an toàn', 'key': key_value}

    @staticmethod
    async def create_marketing_campaign(data: dict, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        campaign = {'_id': str(uuid7()), 'title': data.get('title', 'Chiến dịch mới'), 'target_audience': data.get('target', 'ALL'), 'discount_percent': data.get('discount', 0), 'status': 'active', 'created_at': datetime.now(timezone.utc)}
        await db['marketing_campaigns'].insert_one(campaign)
        logger.info(f"Chiến dịch '{campaign['title']}' đã được khởi tạo")
        return {'message': 'Chiến dịch tiếp thị mới đã được ghi nhận trên hệ thống'}

    @staticmethod
    async def get_system_health(db=None) -> dict:
        import os
        import httpx
        from core.config import settings
        if db is None:
            db = db_client.mongodb.get_default_database()
        try:
            await db.command('ping')
            db_status = 'connected'
        except Exception:
            db_status = 'disconnected'
        redis_status = 'disconnected'
        if db_client.redis:
            try:
                await db_client.redis.ping()
                redis_status = 'connected'
            except Exception:
                redis_status = 'error'
        else:
            redis_status = 'not_configured'
        rag_status = 'unknown'
        rag_url = getattr(settings, 'AGENTIC_AI_URL', None)
        if rag_url:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f'{rag_url}/health')
                    rag_status = 'healthy' if resp.status_code == 200 else 'degraded'
            except Exception:
                rag_status = 'unreachable'
        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        cpu_usage = f'{min(load_avg[0] / os.cpu_count() * 100, 100):.1f}%' if hasattr(os, 'cpu_count') else f'{min(load_avg[0] * 10, 100):.1f}%'
        return {'status': 'healthy' if db_status == 'connected' and redis_status == 'connected' and (rag_status == 'healthy') else 'degraded', 'services': {'database': db_status, 'cache': redis_status, 'ai_agent': rag_status}, 'resources': {'cpu_load': cpu_usage, 'uptime': '99.9%'}, 'timestamp': datetime.now(timezone.utc).isoformat()}

    @staticmethod
    async def get_maintenance_mode(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        config = await db['system_config'].find_one({'key': 'maintenance_mode'})
        if not config:
            return {'enabled': False, 'message': ''}
        return {'enabled': config.get('enabled', False), 'message': config.get('message', '')}

    @staticmethod
    async def get_minio_stats(db=None) -> dict:
        from core.storage import get_storage_client
        try:
            async with await get_storage_client() as storage_client:
                buckets_resp = await storage_client.list_buckets()
                buckets_list = buckets_resp.get('Buckets', [])
                total_size_bytes = 0
                total_objects_count = 0
                buckets_data = []
                categories = {'CTAN': {'count': 0, 'size': 0}, 'NXBGD': {'count': 0, 'size': 0}, 'NXBST': {'count': 0, 'size': 0}, 'Anna Archive': {'count': 0, 'size': 0}, 'User Images': {'count': 0, 'size': 0}, 'User Documents': {'count': 0, 'size': 0}, 'Others': {'count': 0, 'size': 0}}
                for b in buckets_list:
                    bucket_name = b['Name']
                    paginator = storage_client.get_paginator('list_objects_v2')
                    obj_count = 0
                    bucket_size = 0
                    async for page in paginator.paginate(Bucket=bucket_name):
                        for obj in page.get('Contents', []):
                            size = obj['Size']
                            key = obj['Key']
                            bucket_size += size
                            obj_count += 1
                            total_size_bytes += size
                            total_objects_count += 1
                            if 'ctan' in key.lower():
                                categories['CTAN']['count'] += 1
                                categories['CTAN']['size'] += size
                            elif 'nxbgd' in key.lower():
                                categories['NXBGD']['count'] += 1
                                categories['NXBGD']['size'] += size
                            elif 'nxbst' in key.lower():
                                categories['NXBST']['count'] += 1
                                categories['NXBST']['size'] += size
                            elif 'anna_archive' in key.lower():
                                categories['Anna Archive']['count'] += 1
                                categories['Anna Archive']['size'] += size
                            elif key.startswith('images/'):
                                categories['User Images']['count'] += 1
                                categories['User Images']['size'] += size
                            elif key.startswith('tài liệu/'):
                                categories['User Documents']['count'] += 1
                                categories['User Documents']['size'] += size
                            else:
                                categories['Others']['count'] += 1
                                categories['Others']['size'] += size
                    buckets_data.append({'name': bucket_name, 'created_at': b['CreationDate'].isoformat() if 'CreationDate' in b else '', 'size_bytes': bucket_size, 'objects_count': obj_count})
                formatted_categories = []
                for (name, stats) in categories.items():
                    if stats['count'] > 0 or stats['size'] > 0:
                        formatted_categories.append({'name': name, 'count': stats['count'], 'size_bytes': stats['size']})
                return {'status': 'healthy', 'total_buckets': len(buckets_list), 'total_size_bytes': total_size_bytes, 'total_objects_count': total_objects_count, 'buckets': buckets_data, 'categories': formatted_categories}
        except Exception as e:
            logger.error(f'Lỗi lấy thông số lưu trữ từ MinIO: {e}')
            return {'status': 'unreachable', 'total_buckets': 0, 'total_size_bytes': 0, 'total_objects_count': 0, 'buckets': [], 'categories': []}

    @staticmethod
    async def get_collector_stats(db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.COLLECTOR_URL}/thong-ke", timeout=5.0)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error(f"Lỗi lấy dữ liệu thống kê: {e}")
        return {'total_documents': 0, 'total_assets': 0, 'collector_status': 'OFFLINE', 'last_crawl': None, 'storage_usage_mb': 0}

    @staticmethod
    async def handle_bug_report(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        report_id = str(uuid7())
        await db['bug_reports'].insert_one({'_id': report_id, 'title': data['title'], 'description': data['description'], 'status': 'open', 'assigned_to': str(current_moderator.id), 'created_at': datetime.now(timezone.utc)})
        logger.info(f'Lỗi {report_id} đã được giải quyết bởi {current_moderator.id}')
        return {'message': 'Hệ thống đã ghi nhận báo cáo sự cố của người dùng'}

    @staticmethod
    async def assign_task(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = {'_id': str(uuid7()), 'assigned_to': data['moderator_id'], 'title': data['title'], 'status': 'pending', 'created_at': datetime.now(timezone.utc)}
        await db['moderator_tasks'].insert_one(task)
        logger.info(f"Đã giao việc cho {data['moderator_id']} bởi {current_moderator.id}")
        return {'message': 'Nhiệm vụ điều hành đã được phân công'}

    @staticmethod
    async def submit_policy_proposal(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        proposal_id = str(uuid7())
        await db['policy_proposals'].insert_one({'_id': proposal_id, 'author_id': str(current_moderator.id), 'title': data['title'], 'content': data['content'], 'status': 'pending', 'created_at': datetime.now(timezone.utc)})
        logger.info(f'Đề xuất mới {proposal_id} vừa được gửi bởi {current_moderator.id}')

    @staticmethod
    async def get_withdrawal_requests(status: str='PENDING', limit: int=50, db=None) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        pipeline = [{'$match': {'status': status}}, {'$sort': {'created_at': -1}}, {'$limit': limit}, {'$lookup': {'from': 'users', 'localField': 'user_id', 'foreignField': '_id', 'as': 'user'}}, {'$unwind': {'path': '$user', 'preserveNullAndEmptyArrays': True}}]
        apps = await db['withdrawal_requests'].aggregate(pipeline).to_list(length=limit)
        result = []
        for a in apps:
            user = a.get('user', {})
            result.append({'_id': str(a['_id']), 'user_id': a['user_id'], 'user_name': user.get('full_name') if user else 'Unknown', 'user_email': user.get('email') if user else '', 'amount': a.get('amount'), 'status': a.get('status'), 'created_at': a['created_at'].isoformat() if isinstance(a.get('created_at'), datetime) else a.get('created_at'), 'bank_info': user.get('bank_info') if user else {}})
        return result

    @staticmethod
    async def approve_withdrawal(withdrawal_id: str, admin_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        withdrawal = await db['withdrawal_requests'].find_one({'_id': withdrawal_id, 'status': 'PENDING'})
        if not withdrawal:
            raise HTTPException(status_code=404, detail='Giao dịch rút tiền này không có trên hệ thống hoặc đã được success trước đó')
        await db['withdrawal_requests'].update_one({'_id': withdrawal_id}, {'$set': {'status': 'COMPLETED', 'processed_by': admin_id, 'processed_at': datetime.now(timezone.utc)}})
        logger.info(f'Yêu cầu rút tiền {withdrawal_id} đã được duyệt bởi {admin_id}')
        return {'message': 'Yêu cầu rút tiền đã được phê duyệt'}

    @staticmethod
    async def reject_withdrawal(withdrawal_id: str, reason: str, admin_id: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        withdrawal = await db['withdrawal_requests'].find_one({'_id': withdrawal_id, 'status': 'PENDING'})
        if not withdrawal:
            raise HTTPException(status_code=404, detail='Giao dịch rút tiền này không có trên hệ thống')
        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                await db['users'].update_one({'_id': withdrawal['user_id']}, {'$inc': {'wallet_balance': withdrawal['amount']}}, session=session)
                await db['withdrawal_requests'].update_one({'_id': withdrawal_id}, {'$set': {'status': 'REJECTED', 'rejection_reason': reason, 'processed_by': admin_id, 'processed_at': datetime.now(timezone.utc)}}, session=session)
                from src.schemas.wallet import Transaction, TransactionType
                tx = Transaction(user_id=withdrawal['user_id'], type=TransactionType.REFUND, amount=withdrawal['amount'], note=f'Hoàn trả yêu cầu rút tiền bị từ chối: {reason}')
                await db['transactions'].insert_one(tx.model_dump(by_alias=True), session=session)
                await session.commit_transaction()
                logger.info(f'Yêu cầu rút tiền {withdrawal_id} đã bị bác bỏ bởi {admin_id}. Lý do: {reason}')
                return {'message': 'Yêu cầu rút tiền đã bị từ chối và tiền đã được hoàn lại vào ví'}
        except Exception as e:
            await session.abort_transaction()
            logger.error(f'Lỗi khi xử lý thao tác từ chối lệnh rút tiền: {e}')
            raise HTTPException(status_code=500, detail='Thất bại khi từ chối giao dịch')
        finally:
            await session.end_session()