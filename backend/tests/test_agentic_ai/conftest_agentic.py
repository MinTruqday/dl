"""
Conftest for agentic_ai unit tests.
Contains all fixtures, mocks, and helpers used across agentic_ai test files.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest




FAKE_TOKEN = "Bearer fake-jwt-admin-token"
FAKE_USER_ID = "test-user-123"
FAKE_DOC_ID = "test-doc-abc"

FAKE_DOC_RESPONSE = {
    "data": {
        "id": FAKE_DOC_ID,
        "title": "Test Document",
        "content": '{"blocks":[{"type":"paragraph","data":{"text":"Hello World"}}],"version":"2.29.1"}',
        "content_format": "json",
        "status": "draft",
        "deleted_at": None,
    }
}

FAKE_PROFILE_RESPONSE = {
    "data": {"full_name": "Test User", "email": "test@example.com"}
}

FAKE_WALLET_RESPONSE = {
    "data": {"balance": 500, "currency": "dl"}
}

FAKE_TRANSACTION_RESPONSE = {
    "data": [
        {"type": "TOPUP", "amount": 100, "note": "First deposit"},
        {"type": "PAYMENT", "amount": 50, "note": "Document purchase"},
    ]
}

FAKE_REVENUE_RESPONSE = {
    "data": {"total_revenue": 1200, "pending_withdrawal": 300}
}

FAKE_DOCUMENTS_LIST = {
    "data": [
        {"title": "Doc 1", "status": "published"},
        {"title": "Doc 2", "status": "draft"},
    ]
}

FAKE_TRASH_DOCUMENTS = {
    "data": [
        {"title": "Deleted Doc", "deleted_at": "2024-01-01T00:00:00Z"}
    ]
}

FAKE_ANALYTICS_RESPONSE = {
    "data": {"readers_started": 150, "dropoff_rate": 34.5}
}

FAKE_DEPOSIT_RESPONSE = {
    "data": {
        "checkout_url": "https://pay.test.com/checkout/abc123",
        "payment_url": None,
    }
}

FAKE_VOUCHER_RESPONSE = {
    "data": {"bonus_dl": 200}
}




def make_mock_response(status_code: int, data: dict) -> MagicMock:
    """Create a mock httpx.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json = MagicMock(return_value=data)
    return mock_resp




@pytest.fixture
def mock_api_request():
    """Fixture that patches _make_api_request in tools.interface."""
    with patch("src.tools.interface._make_api_request") as mock_req:
        yield mock_req


@pytest.fixture
def valid_token() -> str:
    return FAKE_TOKEN


@pytest.fixture
def admin_config() -> dict:
    """RunnableConfig with an admin Bearer token."""
    return {"configurable": {"token": FAKE_TOKEN}}


@pytest.fixture
def no_auth_config() -> dict:
    """RunnableConfig with no token (unauthenticated)."""
    return {"configurable": {}}


@pytest.fixture
def non_admin_config() -> dict:
    """RunnableConfig with a non-admin token (admin check will fail)."""
    return {"configurable": {"token": "Bearer non-admin-token"}}
