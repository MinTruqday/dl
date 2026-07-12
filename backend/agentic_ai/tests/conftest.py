import pytest
import pytest_asyncio
import httpx
import os

BASE_URL = "http://doclib_agentic_ai:8000"
AUTH_URL = "http://doclib_authentication:8000/xac-thuc/dang-nhap"

@pytest_asyncio.fixture(scope="function")
async def auth_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            AUTH_URL,
            data={"username": "admin@doclib.com", "password": "123456"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            return data["data"]["access_token"]
        else:
            pytest.fail(f"Failed to obtain auth token: {response.text}")

@pytest_asyncio.fixture(scope="function")
async def api_client(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=120.0) as client:
        yield client
