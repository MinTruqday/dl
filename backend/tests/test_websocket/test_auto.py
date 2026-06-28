"""
Auto-generated tests for websocket based on OpenAPI schema.
"""

import pytest
import httpx
from typing import AsyncGenerator

pytestmark = pytest.mark.asyncio(loop_scope='session')

async def test_auto_health_check_health_get(websocket_client):
    """Test for GET /health"""
    response = await websocket_client.get('/health')

    assert response.status_code < 500
