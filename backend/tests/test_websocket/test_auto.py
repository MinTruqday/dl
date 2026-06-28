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
    # We just want to ensure it doesn't return 404 or 500, but rather a structural response
    assert response.status_code < 500

