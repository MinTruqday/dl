from typing import Any, Optional, List
from core.database import db_client
from core.publication import publish_event
from fastapi import HTTPException
from loguru import logger
import uuid
from uuid6 import uuid7
from datetime import datetime, timezone

class CollectorService:

    @staticmethod
    async def trigger_collection(source: str, pages: Optional[int]=1, db=None):
        if not db_client.rabbitmq:
            raise HTTPException(status_code=503, detail='Dịch vụ hàng đợi RabbitMQ hiện không sẵn sàng.')
        try:
            await CollectorService.stop_collection()
        except Exception:
            pass
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
            raise HTTPException(status_code=400, detail=f"Nguồn thu thập '{source}' không được hỗ trợ.")
        success = await publish_event(queue_name, payload)
        if not success:
            raise HTTPException(status_code=500, detail='Không thể gửi lệnh thu thập vào hàng đợi xử lý.')
        logger.info(f"Collection job {payload['job_id']} triggered for source {source}")
        return {'status': 'success', 'job_id': payload['job_id'], 'message': f'Đã kích hoạt tiến trình thu thập dữ liệu từ {source}.'}

    @staticmethod
    async def stop_collection(db=None):
        if not db_client.rabbitmq:
            raise HTTPException(status_code=503, detail='Dịch vụ hàng đợi RabbitMQ hiện không sẵn sàng.')
        try:
            channel = await db_client.rabbitmq.channel()
            queues = ['collect_list_queue', 'collect_detail_queue', 'download_processor_queue', 'nxbgd_queue', 'nxbst_queue', 'anna_archive_queue', 'ctan_queue']
            for q_name in queues:
                try:
                    queue = await channel.declare_queue(q_name, durable=True)
                    await queue.purge()
                except Exception as ex:
                    logger.warning(f'Could not purge queue {q_name}: {ex}')
            await channel.close()
            logger.info('Purged all collector queues')
            return {'status': 'success', 'message': 'Đã dừng và làm sạch toàn bộ hàng đợi thu thập.'}
        except Exception as e:
            logger.error(f'Failed to purge queues: {e}')
            raise HTTPException(status_code=500, detail='Lỗi khi làm sạch hàng đợi.')

    @staticmethod
    async def get_collector_stats(db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()
        total_collected = await db['documents'].count_documents({'author_id': {'$regex': '.*collector.*'}})
        return {'total_documents_collected': total_collected, 'active_sources': ['AnnaArchive', 'NXBST', 'NXBGD', 'CTAN'], 'status': 'operational'}