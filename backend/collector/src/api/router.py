from fastapi import APIRouter, HTTPException
from loguru import logger
import os
from uuid6 import uuid7
from datetime import datetime, timezone
from src.schemas.collector import CollectionRequest
from src.core.mq import mq_client
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

@router.post('/kich-hoat')
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
        raise HTTPException(status_code=400, detail=f"Nguồn thu thập '{source}' không được hỗ trợ")
        
    try:
        await mq_client.publish(queue_name, payload)
        logger.info(f"Collection job {payload['job_id']} triggered for source {source}")
        return {'status': 'success', 'job_id': payload['job_id'], 'message': f'Đã kích hoạt tiến trình thu thập dữ liệu từ {source}.'}
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}")
        raise HTTPException(status_code=500, detail='Không thể gửi lệnh thu thập vào hàng đợi xử lý')

@router.post('/dung')
async def stop_collection():
    try:
        if mq_client.channel:
            await mq_client.channel.close()
        logger.info('Collection paused. Existing queue messages preserved.')
        return {'status': 'success', 'message': 'Đã gửi tín hiệu dừng thu thập'}
    except Exception as e:
        logger.error(f'Failed to pause collection: {e}')
        raise HTTPException(status_code=500, detail='Lỗi khi gửi lệnh dừng thu thập')

@router.get('/thong-ke')
async def get_collector_stats():
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/doclib")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_default_database()
    total_collected = await db['documents'].count_documents({'author_id': {'$regex': '.*collector.*'}})
    return {'total_documents_collected': total_collected, 'active_sources': ['AnnaArchive', 'NXBST', 'NXBGD', 'CTAN'], 'status': 'operational'}

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
