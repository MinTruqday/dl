from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Optional, List, Union
import redis.asyncio as aioredis
from src.core.infrastructure.configuration import settings

router = APIRouter()

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_uri = settings.REDIS_URI if hasattr(settings, 'REDIS_URI') else 'redis://doclib_redis:6379/0'
        redis_client = aioredis.from_url(redis_uri, decode_responses=True)
    return redis_client

class SetRequest(BaseModel):
    key: str
    value: Any
    expire: Optional[int] = None

class GetRequest(BaseModel):
    key: str

class DeleteRequest(BaseModel):
    key: str

class SaddRequest(BaseModel):
    key: str
    member: str

class SismemberRequest(BaseModel):
    key: str
    member: str

class PublishRequest(BaseModel):
    channel: str
    message: str

class PipelineIncrRequest(BaseModel):
    key: str
    expire: int

@router.post("/set")
async def cache_set(req: SetRequest):
    r = await get_redis()
    if req.expire:
        res = await r.setex(req.key, req.expire, str(req.value))
    else:
        res = await r.set(req.key, str(req.value))
    return {"success": res}

@router.post("/get")
async def cache_get(req: GetRequest):
    r = await get_redis()
    val = await r.get(req.key)
    return {"value": val}

@router.post("/delete")
async def cache_delete(req: DeleteRequest):
    r = await get_redis()
    res = await r.delete(req.key)
    return {"deleted": res}

@router.post("/sadd")
async def cache_sadd(req: SaddRequest):
    r = await get_redis()
    res = await r.sadd(req.key, req.member)
    return {"added": res}

@router.post("/sismember")
async def cache_sismember(req: SismemberRequest):
    r = await get_redis()
    res = await r.sismember(req.key, req.member)
    return {"is_member": res}

@router.post("/smembers")
async def cache_smembers(req: GetRequest):
    r = await get_redis()
    res = await r.smembers(req.key)
    return {"members": list(res)}

@router.post("/publish")
async def cache_publish(req: PublishRequest):
    r = await get_redis()
    res = await r.publish(req.channel, req.message)
    return {"receivers": res}

@router.post("/pipeline_incr")
async def cache_pipeline_incr(req: PipelineIncrRequest):
    r = await get_redis()
    pipe = r.pipeline()
    pipe.incr(req.key)
    pipe.expire(req.key, req.expire)
    res = await pipe.execute()
    return {"values": res}

