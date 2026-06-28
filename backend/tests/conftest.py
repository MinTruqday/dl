import pytest
import pytest_asyncio
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis
from uuid6 import uuid7
import os
import json

SERVICES = {
    'authentication': 8500,
    'management': 8050,
    'cloud': 8700,
    'content': 8450,
    'drm': 8600,
    'compilation': 8300,
    'notification': 8150,
    'payment': 8350,
    'websocket': 8200
}

SECRET_KEY = os.getenv("SECRET_KEY", "doclib-password")
ALGORITHM = "HS256"

@pytest.fixture(scope="session")
def admin_uid():
    return str(uuid7())

@pytest.fixture(scope="session")
def admin_session_id():
    return str(uuid7())

@pytest.fixture(scope="session")
def admin_email():
    return "admin_test@doclib.vn"

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_admin_user(admin_uid, admin_session_id, admin_email):
    # Setup Mongo
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017/")
    db = mongo_client["doclib_authentication"]
    
    admin_user = {
        "_id": admin_uid,
        "email": admin_email,
        "full_name": "Admin Test User",
        "role": "admin",
        "is_active": True,
        "is_premium": True,
        "permissions": ["all"],
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.update_one({"_id": admin_uid}, {"$set": admin_user}, upsert=True)
    
    # Setup Redis
    r = await aioredis.from_url("redis://localhost:6379/0", decode_responses=True)
    await r.sadd(f"user_sessions:{admin_uid}", admin_session_id)
    
    yield
    
    # Teardown
    await db.users.delete_one({"_id": admin_uid})
    await r.srem(f"user_sessions:{admin_uid}", admin_session_id)
    mongo_client.close()
    await r.aclose()

@pytest.fixture(scope="session")
def admin_token(admin_uid, admin_session_id, admin_email):
    payload = {
        "sub": admin_email,
        "uid": admin_uid,
        "sid": admin_session_id,
        "role": "admin",
        "full_name": "Admin Test User",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest_asyncio.fixture(scope="session")
async def authentication_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8500", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def management_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8050", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def cloud_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8700", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def content_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8450", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def drm_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8600", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def compilation_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8300", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def notification_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8150", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def payment_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8350", headers=auth_headers, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="session")
async def websocket_client(auth_headers):
    async with httpx.AsyncClient(base_url=f"http://localhost:8200", headers=auth_headers, timeout=10.0) as client:
        yield client

