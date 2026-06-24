import os

BACKEND_DIR = "backend"

mq_content = """import asyncio
import json
import uuid
import aio_pika
from loguru import logger
from typing import Any, Dict, Optional
from src.core.infrastructure.configuration import settings

class RabbitMQClient:
    def __init__(self):
        self.url = settings.RABBITMQ_URI
        self.connection = None
        self.channel = None
        self.pending_acks = {}

    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return

        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                logger.info("Kết nối RabbitMQ thành công")
                return
            except Exception as e:
                logger.error(f"Lỗi kết nối RabbitMQ, đang thử lại: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(3)

    async def get_queue(self, queue_name: str):
        if not self.channel:
            await self.connect()
        # Declare dead-letter exchange
        dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
        dlq = await self.channel.declare_queue("dlq", durable=True)
        await dlq.bind(dlx, "dlq")
        queue_args = {
            "x-dead-letter-exchange": "dlx",
            "x-dead-letter-routing-key": "dlq",
        }
        return await self.channel.declare_queue(queue_name, durable=True, arguments=queue_args)

    async def publish(self, queue_name: str, payload: dict) -> bool:
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            return True
        except Exception as e:
            logger.error(f"Lỗi phân phối tin nhắn: {e}")
            return False

    async def consume(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.channel:
            await self.connect()
        queue = await self.get_queue(queue_name)
        try:
            message = await queue.get(timeout=timeout)
            if message:
                payload = json.loads(message.body.decode())
                ack_id = str(uuid.uuid4())
                
                self.pending_acks[ack_id] = message
                
                # Auto NACK task
                asyncio.create_task(self._auto_nack_if_timeout(ack_id, delay=300))
                
                return {
                    "payload": payload,
                    "delivery_tag": ack_id
                }
            return None
        except aio_pika.exceptions.QueueEmpty:
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy tin nhắn: {e}")
            return None

    async def _auto_nack_if_timeout(self, ack_id: str, delay: int):
        await asyncio.sleep(delay)
        message = self.pending_acks.pop(ack_id, None)
        if message:
            logger.warning(f"Timeout! Không thấy ai ACK, NACK tin nhắn {ack_id} để retry.")
            try:
                await message.nack(requeue=True)
            except Exception as e:
                pass

    async def ack(self, delivery_tag: str) -> bool:
        message = self.pending_acks.pop(delivery_tag, None)
        if message:
            try:
                await message.ack()
                return True
            except Exception as e:
                logger.error(f"Lỗi ACK tin nhắn: {e}")
                return False
        return False

    async def health_check(self) -> bool:
        try:
            await self.connect()
            return True
        except Exception:
            return False

    async def aclose(self):
        if self.connection:
            await self.connection.close()

mq = RabbitMQClient()
"""

redis_client_content = """import json
import redis.asyncio as redis
from loguru import logger
from src.core.infrastructure.configuration import settings

class RedisAPIClient:
    def __init__(self):
        self.url = settings.REDIS_URI
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client

    async def set(self, key: str, value: str):
        try:
            return await self.get_client().set(key, value)
        except Exception as e:
            logger.error(f"Redis Cache Server Error SET {key}: {e}")
            raise Exception("Cache service unavailable")

    async def setex(self, key: str, expire: int, value: str):
        try:
            return await self.get_client().setex(key, expire, value)
        except Exception as e:
            logger.error(f"Redis Cache Server Error SETEX {key}: {e}")
            raise Exception("Cache service unavailable")

    async def get(self, key: str):
        try:
            return await self.get_client().get(key)
        except Exception as e:
            logger.error(f"Redis Cache Server Error GET {key}: {e}")
            raise Exception("Cache service unavailable")

    async def delete(self, key: str):
        try:
            return await self.get_client().delete(key)
        except Exception as e:
            logger.error(f"Redis Cache Server Error DELETE {key}: {e}")
            raise Exception("Cache service unavailable")

    async def sadd(self, key: str, member: str):
        try:
            return await self.get_client().sadd(key, member)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def sismember(self, key: str, member: str):
        try:
            return await self.get_client().sismember(key, member)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def smembers(self, key: str):
        try:
            return await self.get_client().smembers(key)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def publish(self, channel: str, message: str):
        try:
            return await self.get_client().publish(channel, message)
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def pipeline_incr_expire(self, key: str, expire: int):
        try:
            client = self.get_client()
            async with client.pipeline() as pipe:
                await pipe.incr(key)
                await pipe.expire(key, expire)
                res = await pipe.execute()
                return res
        except Exception as e:
            raise Exception("Cache service unavailable")

    async def aclose(self):
        if self._client:
            await self._client.aclose()

redis_client = RedisAPIClient()
"""

mongo_content = """from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

class MongoClient:
    def __init__(self):
        self.db_name = settings.SERVICE_DB_NAME

    def get_db(self):
        if not database.mongodb:
            raise Exception("MongoDB is not initialized")
        return database.mongodb[self.db_name]

    async def find_one(self, collection: str, query: dict, projection: dict = None):
        return await self.get_db()[collection].find_one(query, projection)

    async def find(self, collection: str, query: dict, projection: dict = None, sort=None, skip: int = 0, limit: int = 0):
        cursor = self.get_db()[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    async def insert_one(self, collection: str, document: dict):
        return await self.get_db()[collection].insert_one(document)

    async def update_one(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        return await self.get_db()[collection].update_one(filter, update, upsert=upsert)

    async def update_many(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        return await self.get_db()[collection].update_many(filter, update, upsert=upsert)

    async def delete_one(self, collection: str, filter: dict):
        return await self.get_db()[collection].delete_one(filter)

    async def delete_many(self, collection: str, filter: dict):
        return await self.get_db()[collection].delete_many(filter)

    async def count_documents(self, collection: str, filter: dict = {}):
        return await self.get_db()[collection].count_documents(filter)

    async def aggregate(self, collection: str, pipeline: list):
        cursor = self.get_db()[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)

class QueryBuilder:
    def __init__(self, client, collection: str):
        self.client = client
        self.collection = collection
        self._query = {}
        self._sort = None
        self._skip = 0
        self._limit = 0

    def filter(self, query: dict):
        self._query = query
        return self

    def sort(self, *args):
        if len(args) == 2 and isinstance(args[0], str):
            self._sort = [args]
        else:
            self._sort = args[0]
        return self

    def skip(self, s: int):
        self._skip = s
        return self

    def limit(self, l: int):
        self._limit = l
        return self

    async def execute(self):
        return await self.client.find(self.collection, self._query, sort=self._sort, skip=self._skip, limit=self._limit)

    def query(self, collection: str):
        return QueryBuilder(self, collection)

mongo = MongoClient()
"""

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        if f == "mq.py" and "core/infrastructure" in root:
            filepath = os.path.join(root, f)
            with open(filepath, "w") as fp:
                fp.write(mq_content)
        elif f == "redis_client.py" and "core/infrastructure" in root:
            filepath = os.path.join(root, f)
            with open(filepath, "w") as fp:
                fp.write(redis_client_content)
        elif f == "mongo.py" and "core/infrastructure" in root:
            filepath = os.path.join(root, f)
            with open(filepath, "w") as fp:
                fp.write(mongo_content)
                
print("Infrastructure rewrites completed.")
