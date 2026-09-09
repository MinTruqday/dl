import asyncio
import json
from types import SimpleNamespace

from src.agents.react import acting
from src.agents.react.tools import ToolResult


class BoundModel:
    async def ainvoke(self, messages):
        return SimpleNamespace(
            tool_calls=[
                {
                    "name": "read_document",
                    "args": {"document_id": "DOC-1"},
                }
            ],
            invalid_tool_calls=[],
            content="",
        )


class Model:
    def __init__(self):
        self.tools = []
        self.choice = None

    def bind_tools(self, tools, tool_choice=None):
        self.tools = tools
        self.choice = tool_choice
        return BoundModel()


class Executor:
    def __init__(self):
        self.call = None

    async def execute(self, tool_name, session_id, params, config):
        self.call = {
            "tool_name": tool_name,
            "session_id": session_id,
            "params": params,
            "config": config,
        }
        return ToolResult(
            success=True,
            data={"status": "success", "document_id": params["document_id"]},
            duration_ms=4,
        )


def test_agent_selects_and_executes_read_tool(monkeypatch):
    model = Model()
    executor = Executor()
    monkeypatch.setattr(acting, "llm", model)
    monkeypatch.setattr(acting.actor, "tool_executor", executor)

    raw = asyncio.run(
        acting.actor.execute(
            action="Đọc tài liệu DOC-1",
            params={"document_id": "DOC-1"},
            user_id="USER-1",
            token="test-token",
            session_id="SESSION-1",
        )
    )
    result = json.loads(raw)

    assert [tool.name for tool in model.tools] == ["read_document"]
    assert model.choice == "read_document"
    assert executor.call["tool_name"] == "read_document"
    assert executor.call["params"] == {"document_id": "DOC-1"}
    assert executor.call["config"]["configurable"]["token"] == "Bearer test-token"
    assert result == {"status": "success", "document_id": "DOC-1"}


def test_agent_rejects_tool_use_without_authentication():
    raw = asyncio.run(
        acting.actor.execute(
            action="Đọc tài liệu DOC-1",
            params={"document_id": "DOC-1"},
            user_id="USER-1",
        )
    )

    assert json.loads(raw) == {"status": "authentication_required"}
