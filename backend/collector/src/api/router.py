from core.config import settings
from fastapi import APIRouter, HTTPException
from loguru import logger
import os
from uuid6 import uuid7
from datetime import datetime, timezone
from src.schemas.collector import CollectionRequest
from src.core.mq import mq_client
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

@router.post('/noi-bo/kich-hoat')
async def trigger_collection(req: CollectionRequest):
    source = req.source
    pages = req.pages
    payload = {'source': source, 'job_id': str(uuid7()), 'triggered_at': datetime.now(timezone.utc).isoformat()}
    queue_name = ''
    if source == 'AnnaArchive':
        queue_name = 'anna_archive_queue'
        payload['pages'] = pages
    elif source == 'NXBST':
        queue_name = 'nxbst_queue'
        payload['pages'] = pages
    elif source == 'NXBGD':
        queue_name = 'nxbgd_queue'
        payload['pages'] = pages
    elif source == 'CTAN':
        queue_name = 'ctan_queue'
        payload['pages'] = pages
    else:
        raise HTTPException(status_code=400, detail=f"Nguồn dữ liệu '{source}' hiện chưa được hệ thống hỗ trợ")
        
    try:
        await mq_client.publish(queue_name, payload)
        logger.info(f"Tiến trình thu thập {payload['job_id']} đã được bật cho nguồn {source}")
        return {'status': 'success', 'job_id': payload['job_id'], 'message': f'Tiến trình thu thập dữ liệu đã được khởi chạy thành công cho nguồn {source}'}
    except Exception as e:
        logger.error(f"Bật tiến trình thu thập bị lỗi: {e}")
        raise HTTPException(status_code=500, detail='Hệ thống không thể chuyển lệnh thu thập vào hàng đợi xử lý')

@router.post('/dung')
async def stop_collection():
    try:
        if mq_client.channel:
            await mq_client.channel.close()
        logger.info('Đã tạm ngưng thu thập. Các tác vụ trong hàng chờ vẫn được bảo lưu nhé')
        return {'status': 'success', 'message': 'Tín hiệu dừng thu thập đã được hệ thống tiếp nhận'}
    except Exception as e:
        logger.error(f'Tạm dừng thu thập bị lỗi: {e}')
        raise HTTPException(status_code=500, detail='Quá trình truyền tín hiệu dừng thu thập gặp sự cố')

@router.get('/noi-bo/cong-viec-dang-chay')
async def get_active_jobs():
    mongo_uri = settings.MONGODB_URI
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_default_database()
    active_collectors = await db['collection_jobs'].find({'status': {'$in': ['running', 'pending']}}).to_list(50)
    jobs = [{'id': str(j['_id']), 'progress': j.get('progress', 0), 'status': j['status']} for j in active_collectors]
    return jobs

@router.get('/thong-ke')
async def get_collector_stats():
    mongo_uri = settings.MONGODB_URI
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_default_database()
    total_docs = await db['documents'].count_documents({})
    total_assets = await db['archives'].count_documents({})
    recent_crawls = await db['documents'].find({}, {'created_at': 1}).sort('created_at', -1).limit(1).to_list(length=1)
    last_crawl = recent_crawls[0]['created_at'].isoformat() if recent_crawls and isinstance(recent_crawls[0].get('created_at'), datetime) else None
    total_collected = await db['documents'].count_documents({'author_id': {'$regex': '.*collector.*'}})
    return {
        'total_documents': total_docs,
        'total_assets': total_assets,
        'collector_status': 'RUNNING',
        'last_crawl': last_crawl,
        'storage_usage_mb': round(total_docs * 0.1, 2),
        'total_documents_collected': total_collected,
        'active_sources': ['AnnaArchive', 'NXBST', 'NXBGD', 'CTAN'],
        'status': 'operational'
    }

@router.get('/logs')
async def get_collector_logs():
    log_file = 'logs/backend.log'
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            filtered_lines = []
            whitelist = ['pipelines.nxbgd', 'pipelines.anna', 'pipelines.nxbst', 'pipelines.ctan', 'services.collector', '[NXBGD', '[NXBST', '[CTAN', '[Anna', 'Collector']
            for line in lines:
                if any((kw.lower() in line.lower() for kw in whitelist)):
                    filtered_lines.append(line)
            logs = filtered_lines[-50:]
    return logs
