from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/mongo")

# Global client
client: Optional[AsyncIOMotorClient] = None

def get_client():
    global client
    if client is None:
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), maxPoolSize=1000)
    return client

class QueryRequest(BaseModel):
    db: str
    collection: str
    query: Dict[str, Any] = {}
    projection: Optional[Dict[str, Any]] = None
    sort: Optional[List[tuple]] = None
    limit: int = 0
    skip: int = 0

class InsertOneRequest(BaseModel):
    db: str
    collection: str
    document: Dict[str, Any]

class UpdateOneRequest(BaseModel):
    db: str
    collection: str
    filter: Dict[str, Any]
    update: Dict[str, Any]
    upsert: bool = False

class UpdateManyRequest(BaseModel):
    db: str
    collection: str
    filter: Dict[str, Any]
    update: Dict[str, Any]
    upsert: bool = False

class DeleteOneRequest(BaseModel):
    db: str
    collection: str
    filter: Dict[str, Any]

class DeleteManyRequest(BaseModel):
    db: str
    collection: str
    filter: Dict[str, Any]

class AggregateRequest(BaseModel):
    db: str
    collection: str
    pipeline: List[Dict[str, Any]]

class CountRequest(BaseModel):
    db: str
    collection: str
    filter: Dict[str, Any] = {}

def process_object_ids(data):
    if isinstance(data, dict):
        if "$oid" in data:
            from bson import ObjectId
            return ObjectId(data["$oid"])
        return {k: process_object_ids(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_object_ids(i) for i in data]
    return data

def serialize_object_ids(data):
    from bson import ObjectId
    if isinstance(data, dict):
        return {k: serialize_object_ids(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_object_ids(i) for i in data]
    elif isinstance(data, ObjectId):
        return {"$oid": str(data)}
    return data

@router.post("/find")
async def find_documents(req: QueryRequest):
    c = get_client()
    col = c[req.db][req.collection]
    query = process_object_ids(req.query)
    cursor = col.find(query, req.projection)
    if req.sort:
        cursor = cursor.sort(req.sort)
    if req.skip:
        cursor = cursor.skip(req.skip)
    if req.limit:
        cursor = cursor.limit(req.limit)
    docs = await cursor.to_list(length=req.limit or None)
    return {"data": serialize_object_ids(docs)}

@router.post("/find_one")
async def find_one_document(req: QueryRequest):
    c = get_client()
    col = c[req.db][req.collection]
    query = process_object_ids(req.query)
    doc = await col.find_one(query, req.projection)
    return {"data": serialize_object_ids(doc)}

@router.post("/insert_one")
async def insert_one_document(req: InsertOneRequest):
    c = get_client()
    col = c[req.db][req.collection]
    doc = process_object_ids(req.document)
    result = await col.insert_one(doc)
    return {"inserted_id": serialize_object_ids(result.inserted_id)}

@router.post("/update_one")
async def update_one_document(req: UpdateOneRequest):
    c = get_client()
    col = c[req.db][req.collection]
    filter_query = process_object_ids(req.filter)
    update = process_object_ids(req.update)
    result = await col.update_one(filter_query, update, upsert=req.upsert)
    return {"matched_count": result.matched_count, "modified_count": result.modified_count, "upserted_id": serialize_object_ids(result.upserted_id)}

@router.post("/update_many")
async def update_many_documents(req: UpdateManyRequest):
    c = get_client()
    col = c[req.db][req.collection]
    filter_query = process_object_ids(req.filter)
    update = process_object_ids(req.update)
    result = await col.update_many(filter_query, update, upsert=req.upsert)
    return {"matched_count": result.matched_count, "modified_count": result.modified_count, "upserted_id": serialize_object_ids(result.upserted_id)}

@router.post("/delete_one")
async def delete_one_document(req: DeleteOneRequest):
    c = get_client()
    col = c[req.db][req.collection]
    filter_query = process_object_ids(req.filter)
    result = await col.delete_one(filter_query)
    return {"deleted_count": result.deleted_count}

@router.post("/delete_many")
async def delete_many_document(req: DeleteManyRequest):
    c = get_client()
    col = c[req.db][req.collection]
    filter_query = process_object_ids(req.filter)
    result = await col.delete_many(filter_query)
    return {"deleted_count": result.deleted_count}

@router.post("/aggregate")
async def aggregate_documents(req: AggregateRequest):
    c = get_client()
    col = c[req.db][req.collection]
    pipeline = process_object_ids(req.pipeline)
    cursor = col.aggregate(pipeline)
    docs = await cursor.to_list(length=None)
    return {"data": serialize_object_ids(docs)}

@router.post("/count_documents")
async def count_documents(req: CountRequest):
    c = get_client()
    col = c[req.db][req.collection]
    filter_query = process_object_ids(req.filter)
    count = await col.count_documents(filter_query)
    return {"count": count}
