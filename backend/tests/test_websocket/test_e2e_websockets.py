import sys
import os
import jwt
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from starlette.websockets import WebSocketDisconnect


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../websocket"))

from src.main import app
from src.core.infrastructure.configuration import settings

client = TestClient(app)

@pytest.fixture
def valid_token():
    payload = {"sub": "user_123"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def test_message_socket_authentication_no_token():
    """Test that connection is closed with 1008 if no token provided"""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/user_123"):
            pass
    assert exc_info.value.code == 1008

def test_message_socket_authentication_wrong_user(valid_token):
    """Test that connection is closed with 1008 if token user doesn't match URL user_id"""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/user_456?token={valid_token}"):
            pass
    assert exc_info.value.code == 1008

def test_message_socket_authentication_success(valid_token):
    """Test successful connection when token and user_id match"""
    with patch("src.api.message.database.redis") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)

        with client.websocket_connect(f"/user_123?token={valid_token}") as websocket:
            websocket.send_text("Hello E2E")

            assert websocket is not None

def test_message_socket_authentication_banned_user(valid_token):
    """Test that banned user gets disconnected"""
    with patch("src.api.message.database.redis") as mock_redis:
        mock_redis.get = AsyncMock(return_value=b"1")

        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/user_123?token={valid_token}"):
                pass
        assert exc_info.value.code == 1008

def test_crdt_broadcast_multiple_clients():
    """Test broadcasting between two clients on the same document"""
    with client.websocket_connect("/crdt/doc_xyz") as websocket_alice:
        with client.websocket_connect("/crdt/doc_xyz") as websocket_bob:

            websocket_alice.send_bytes(b"crdt_op_1")


            data = websocket_bob.receive_bytes()
            assert data == b"crdt_op_1"


            websocket_bob.send_bytes(b"crdt_op_2")


            data2 = websocket_alice.receive_bytes()
            assert data2 == b"crdt_op_2"
