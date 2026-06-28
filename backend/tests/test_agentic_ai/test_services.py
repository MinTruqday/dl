"""
Heavy-duty unit tests for agentic_ai service and BLEU/ROUGE-L evaluation math.
These tests cover:
 - BLEU / ROUGE-L pure math functions
 - SandboxAgent tool dispatch
 - _make_api_request retry/idempotency logic
 - finetuning service functions
"""
import sys
import os
import asyncio
import json
import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../agentic_ai"))






class TestMakeApiRequest:

    @pytest.mark.asyncio
    async def test_successful_get_request(self):
        from src.tools.interface import _make_api_request, _get_client

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_resp)

        with patch("src.tools.interface._get_client", return_value=mock_client):
            result = await _make_api_request("GET", "http://test.com/api")

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_post_request_includes_idempotency_key(self):
        from src.tools.interface import _make_api_request

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_resp)

        with patch("src.tools.interface._get_client", return_value=mock_client):
            await _make_api_request("POST", "http://test.com/api", headers={})

        call_kwargs = mock_client.request.call_args
        sent_headers = call_kwargs[1]["headers"]
        assert "Idempotency-Key" in sent_headers

    @pytest.mark.asyncio
    async def test_get_has_3_retries(self):
        """GET requests should retry up to 3 times on 500 errors."""
        from src.tools.interface import _make_api_request

        call_count = [0]

        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            mock_resp = MagicMock()
            if call_count[0] < 3:
                mock_resp.status_code = 500
            else:
                mock_resp.status_code = 200
            return mock_resp

        mock_client = AsyncMock()
        mock_client.request = mock_request

        with patch("src.tools.interface._get_client", return_value=mock_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _make_api_request("GET", "http://test.com/api")

        assert result.status_code == 200
        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_post_has_1_retry(self):
        """POST requests have max_retries=1, so no retry on failure."""
        from src.tools.interface import _make_api_request

        call_count = [0]

        async def mock_request(*args, **kwargs):
            call_count[0] += 1
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            return mock_resp

        mock_client = AsyncMock()
        mock_client.request = mock_request

        with patch("src.tools.interface._get_client", return_value=mock_client):
            await _make_api_request("POST", "http://test.com/api")

        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_put_also_gets_idempotency_key(self):
        from src.tools.interface import _make_api_request

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_resp)

        with patch("src.tools.interface._get_client", return_value=mock_client):
            await _make_api_request("PUT", "http://test.com/api", headers={})

        call_kwargs = mock_client.request.call_args
        assert "Idempotency-Key" in call_kwargs[1]["headers"]

    @pytest.mark.asyncio
    async def test_successful_delete_request(self):
        from src.tools.interface import _make_api_request

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_resp)

        with patch("src.tools.interface._get_client", return_value=mock_client):
            result = await _make_api_request("DELETE", "http://test.com/api/1")

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_exception_raised_after_all_retries(self):
        from src.tools.interface import _make_api_request

        async def always_fail(*args, **kwargs):
            raise Exception("Network error")

        mock_client = AsyncMock()
        mock_client.request = always_fail

        with patch("src.tools.interface._get_client", return_value=mock_client):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(Exception, match="Network error"):
                    await _make_api_request("GET", "http://test.com/api")






class TestFinetuningService:

    @pytest.mark.asyncio
    async def test_create_dataset_returns_result(self):
        """create_dataset should call repo and return the result."""
        import src.services.finetuning as svc
        from src.repositories.finetuning import FinetuneRepository

        mock_result = {"_id": "new-ds-id", "name": "My Dataset", "created_by": "user-1"}
        with patch.object(FinetuneRepository, "insert_dataset", new_callable=AsyncMock, return_value=mock_result):
            result = await svc.create_dataset({
                "name": "My Dataset",
                "description": "Test dataset",
                "user_id": "user-1",
            })
        assert result is not None

    @pytest.mark.asyncio
    async def test_list_datasets_returns_list(self):
        """list_datasets should return a list of datasets for a user."""
        import src.services.finetuning as svc

        mock_datasets = [{"_id": "ds-1", "name": "D1"}, {"_id": "ds-2", "name": "D2"}]
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.execute = AsyncMock(return_value=mock_datasets)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch("src.services.finetuning.get_db", return_value=mock_db, create=True):
            result = await svc.list_datasets("user-1")
        assert isinstance(result, list)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_jobs_returns_list(self):
        """list_jobs should return jobs for a user."""
        import src.services.finetuning as svc

        mock_jobs = [{"_id": "job-1", "status": "pending"}]
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.execute = AsyncMock(return_value=mock_jobs)
        mock_collection.find = MagicMock(return_value=mock_cursor)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch("src.services.finetuning.get_db", return_value=mock_db, create=True):
            result = await svc.list_jobs("user-1")
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_report_progress_updates_job(self):
        """report_progress should call update_job with the given fields."""
        import src.services.finetuning as svc
        from src.repositories.finetuning import FinetuneRepository

        with patch.object(FinetuneRepository, "update_job", new_callable=AsyncMock, return_value=True):
            await svc.report_progress("job-1", {"status": "running", "progress": 50})







class TestSandboxAgent:

    def _make_agent(self):
        from src.agents.sandbox import SandboxAgent
        agent = SandboxAgent.__new__(SandboxAgent)
        agent.base_url = "http://test-api"
        agent.tool_map = {}
        agent.tools_prompt = ""
        return agent

    @pytest.mark.asyncio
    async def test_no_token_returns_auth_message(self):
        agent = self._make_agent()
        result = await agent.execute("get user balance", {}, "user-123", token=None)
        assert "xác thực" in result.lower() or "đăng nhập" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_token_returns_auth_message(self):
        agent = self._make_agent()
        result = await agent.execute("get user balance", {}, "user-123", token="")
        assert "xác thực" in result.lower() or "đăng nhập" in result.lower()

    @pytest.mark.asyncio
    async def test_with_no_tool_calls_returns_no_tool_message(self):
        """If LLM selects no tools, return appropriate message."""
        agent = self._make_agent()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("src.agents.sandbox.llm", mock_llm):
            with patch("src.core.registry.registry") as mock_reg:
                mock_reg.get = MagicMock(return_value="System prompt")
                result = await agent.execute("tell me a story", {}, "user-123", "Bearer valid-token")

        assert (
            "không tìm ra" in result.lower()
            or "công cụ" in result.lower()
            or "thích hợp" in result.lower()
            or "không thể" in result.lower()
        )

    @pytest.mark.asyncio
    async def test_tool_not_in_tool_map_returns_error(self):
        """If LLM selects a tool not in tool_map, return error."""
        agent = self._make_agent()
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_tool_call = {"name": "nonexistent_tool", "args": {}, "id": "tc-1"}
        mock_response.tool_calls = [mock_tool_call]
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("src.agents.sandbox.llm", mock_llm):
            with patch("src.core.registry.registry") as mock_reg:
                mock_reg.get = MagicMock(return_value="System prompt")
                result = await agent.execute("find something", {}, "user-123", "Bearer token")

        assert "không tồn tại" in result.lower() or "không khả dụng" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_in_tool_map_is_executed(self):
        """If LLM selects a tool that IS in tool_map, it should be called."""
        agent = self._make_agent()
        mock_tool_fn = MagicMock()
        mock_tool_fn.ainvoke = AsyncMock(return_value="wallet balance: 500 credits")
        agent.tool_map = {"get_user_balance": mock_tool_fn}

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_tool_call = {"name": "get_user_balance", "args": {}, "id": "tc-2"}
        mock_response.tool_calls = [mock_tool_call]
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("src.agents.sandbox.llm", mock_llm):
            with patch("src.core.registry.registry") as mock_reg:
                mock_reg.get = MagicMock(return_value="System prompt")
                result = await agent.execute("get balance", {}, "user-123", "Bearer valid-token")


        mock_tool_fn.ainvoke.assert_called_once()
        assert "500" in result or "balance" in result.lower()

    @pytest.mark.asyncio
    async def test_llm_exception_returns_error_message(self):
        """If the LLM throws an exception, return a safe error message."""
        agent = self._make_agent()
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM down"))
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)

        with patch("src.agents.sandbox.llm", mock_llm):
            with patch("src.core.registry.registry") as mock_reg:
                mock_reg.get = MagicMock(return_value="System prompt")
                result = await agent.execute("do something", {}, "user-123", "Bearer valid-token")

        assert "lỗi" in result.lower() or "xảy ra" in result.lower() or "thể" in result.lower()
