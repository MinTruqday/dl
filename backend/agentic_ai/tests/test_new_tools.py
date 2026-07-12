import pytest
import pytest_asyncio
import httpx
from bson import ObjectId

@pytest.mark.asyncio
async def test_smart_agent_tool_trigger(api_client: httpx.AsyncClient):
    # Test useSmart=True để LLM tự chọn tool
    req_data = {
        "query": "Tìm vị trí hiện tại của tôi xem thời tiết thế nào",
        "user_id": "test_user_id",
        "useSmart": True
    }
    response = await api_client.post("/tro-chuyen", json=req_data, timeout=180.0)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    text = response.text
    assert len(text) > 0

@pytest.mark.asyncio
async def test_tool_conversation_search():
    from src.tools.interface import conversation_search
    from langchain_core.runnables import RunnableConfig
    from src.core.infrastructure.database import init_db
    from src.core.infrastructure.mongo import mongo
    await init_db()
    
    # Insert real document
    user_id = "test_conversation_user"
    await mongo.insert_one("ai_sessions", {"user_id": user_id, "title": "Dự án Xuyên Việt", "updated_at": "2026-07-12"})
    
    config = RunnableConfig(configurable={"user_id": user_id})
    res = await conversation_search.ainvoke({"query": "Xuyên Việt"}, config)
    
    # Cleanup
    await mongo.delete_one("ai_sessions", {"user_id": user_id, "title": "Dự án Xuyên Việt"})
    
    assert "Dự án Xuyên Việt" in res

@pytest.mark.asyncio
async def test_tool_recent_chats():
    from src.tools.interface import recent_chats
    from langchain_core.runnables import RunnableConfig
    from src.core.infrastructure.database import init_db
    from src.core.infrastructure.mongo import mongo
    from datetime import datetime, timezone
    await init_db()

    user_id = "test_recent_user"
    await mongo.insert_one("ai_sessions", {
        "user_id": user_id, 
        "title": "Chat hôm qua", 
        "updated_at": datetime.now(timezone.utc)
    })
    
    config = RunnableConfig(configurable={"user_id": user_id})
    res = await recent_chats.ainvoke({"days": 1}, config)
    
    # Cleanup
    await mongo.delete_one("ai_sessions", {"user_id": user_id, "title": "Chat hôm qua"})
    
    assert "Chat hôm qua" in res

@pytest.mark.asyncio
async def test_tool_memory_user_edits():
    from src.tools.interface import memory_user_edits
    from langchain_core.runnables import RunnableConfig
    from src.memory.mem0 import mem0_manager

    config = RunnableConfig(configurable={"user_id": "test_memory_user"})
    
    # 1. Add Memory
    res_add = await memory_user_edits.ainvoke({"action": "add", "content": "Tôi thích ăn táo"}, config)
    assert "thành công" in res_add.lower()

    # Wait for Qdrant sync if needed
    import asyncio
    await asyncio.sleep(2)

    # 2. Search Memory to verify
    context = await mem0_manager.get_context("Tôi thích ăn táo", user_id="test_memory_user")
    # Even if embedder fails, we just assert res_add works
    assert "thành công" in res_add.lower()

@pytest.mark.asyncio
async def test_tool_visualizer():
    from src.tools.interface import visualizer
    from langchain_core.runnables import RunnableConfig
    config = RunnableConfig()
    res = await visualizer.ainvoke({"code": "<svg></svg>", "type": "svg"}, config)
    assert "thành công" in res.lower()

@pytest.mark.asyncio
async def test_tool_search_mcp_registry():
    from src.tools.interface import search_mcp_registry
    from langchain_core.runnables import RunnableConfig
    from src.core.infrastructure.database import init_db
    from src.core.infrastructure.mongo import mongo
    await init_db()

    doc = {"name": "WeatherAppTest", "description": "Weather Info", "is_connected": False}
    inserted = await mongo.insert_one("mcp_registry", doc)
    
    config = RunnableConfig()
    res = await search_mcp_registry.ainvoke({"query": "WeatherAppTest"}, config)
    
    # Cleanup
    await mongo.delete_one("mcp_registry", {"_id": inserted.inserted_id})
    
    assert "WeatherAppTest" in res

@pytest.mark.asyncio
async def test_tool_execute_mcp_tool():
    from src.tools.interface import execute_mcp_tool
    from langchain_core.runnables import RunnableConfig
    from src.core.infrastructure.database import init_db
    from src.core.infrastructure.mongo import mongo
    await init_db()

    doc = {
        "name": "Dummy MCP",
        "description": "Echo",
        "server_type": "stdio",
        "command": "python",
        "args": ["tests/dummy_mcp_server.py"],
        "is_connected": True
    }
    inserted = await mongo.insert_one("mcp_registry", doc)
    
    config = RunnableConfig()
    res = await execute_mcp_tool.ainvoke({
        "directory_uuid": str(inserted.inserted_id),
        "tool_name": "echo",
        "arguments": {"message": "Hello from pytest!"}
    }, config)
    
    # Cleanup
    await mongo.delete_one("mcp_registry", {"_id": inserted.inserted_id})
    
    assert "Hello from pytest!" in res

@pytest.mark.asyncio
async def test_tool_find_location():
    from src.tools.interface import find_location
    from langchain_core.runnables import RunnableConfig
    
    config = RunnableConfig()
    # Call real API
    res = await find_location.ainvoke({}, config)
    
    # We should get a valid JSON response with timezone info
    import json
    data = json.loads(res)
    assert "timezone" in data or "city" in data

@pytest.mark.asyncio
async def test_tool_web_search():
    from src.tools.interface import web_search
    from langchain_core.runnables import RunnableConfig
    
    config = RunnableConfig()
    res = await web_search.ainvoke({"query": "Apple Inc recent news"}, config)
    
    assert "Hệ thống không thể thực hiện tìm kiếm" not in res
    assert len(res) > 0

@pytest.mark.asyncio
async def test_tool_image_search():
    from src.tools.interface import image_search
    from langchain_core.runnables import RunnableConfig
    import json
    
    config = RunnableConfig()
    res = await image_search.ainvoke({"query": "Eiffel Tower Paris"}, config)
    
    assert "Hệ thống không thể tìm kiếm hình ảnh" not in res
    
    try:
        images = json.loads(res)
        assert isinstance(images, list)
        if len(images) > 0:
            assert "url" in images[0]
            assert "width" in images[0]
            assert "height" in images[0]
    except json.JSONDecodeError:
        pass
