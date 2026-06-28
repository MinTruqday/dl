"""
Heavy-duty unit tests for agentic_ai tools (src/tools/interface.py).
Tests every tool with:
 - Happy path (200 responses)
 - Auth failures (no token)
 - API errors (non-200 responses)
 - Edge cases (empty responses, bad input)
"""
import sys
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../agentic_ai"))



_mock_settings = MagicMock()
_mock_settings.INTERNAL_API_URL = "http://internal-api"
_mock_settings.LONG_PROCESS_TIMEOUT = 30.0
_mock_settings.DEFAULT_HTTP_TIMEOUT = 10.0
_mock_settings.SECRET_KEY = "test-secret"
_mock_settings.HF_TOKEN = "hf-fake-token"
_mock_settings.LLAMA_MODEL = "test-model"
_mock_settings.DEFAULT_CHUNK_SIZE = 1000

PATCHER_SETTINGS = patch("src.core.infrastructure.configuration.settings", _mock_settings)
PATCHER_SETTINGS.start()


patch("langchain_huggingface.ChatHuggingFace", MagicMock()).start()
patch("langchain_huggingface.HuggingFaceEndpoint", MagicMock()).start()
patch("langgraph.prebuilt.create_react_agent", MagicMock()).start()


from src.tools.interface import (
    get_user_balance,
    get_transaction_history,
    redeem_voucher,
    get_revenue_report,
    get_my_documents,
    get_trash_documents,
    delete_document,
    restore_document,
    get_document_analytics,
    create_deposit_link,
    create_document,
    read_document,
    update_document,
    translate_document,
    _check_system_access,
    _make_api_request,
)



PATCHER_SETTINGS.stop()




def make_resp(status_code: int, json_data: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json = MagicMock(return_value=json_data)
    return r


ADMIN_CFG = {"configurable": {"token": "Bearer admin-token"}}
NO_AUTH_CFG = {"configurable": {}}






class TestGetUserBalance:

    @pytest.mark.asyncio
    async def test_returns_balance_on_200(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"balance": 300}})
            result = await get_user_balance.ainvoke({}, config=ADMIN_CFG)
        assert "300" in result

    @pytest.mark.asyncio
    async def test_returns_zero_balance(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"balance": 0}})
            result = await get_user_balance.ainvoke({}, config=ADMIN_CFG)
        assert "0" in result

    @pytest.mark.asyncio
    async def test_no_token_returns_auth_message(self):
        result = await get_user_balance.ainvoke({}, config=NO_AUTH_CFG)
        assert "đăng nhập" in result.lower() or "bảo mật" in result.lower() or "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_401_response(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(401, {})
            result = await get_user_balance.ainvoke({}, config=ADMIN_CFG)
        assert "quá hạn" in result.lower() or "đăng nhập" in result.lower()

    @pytest.mark.asyncio
    async def test_500_response_raises_exception(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(500, {})
            with pytest.raises(Exception):
                await get_user_balance.ainvoke({}, config=ADMIN_CFG)






class TestGetTransactionHistory:

    @pytest.mark.asyncio
    async def test_returns_transactions(self):
        transactions = [
            {"type": "TOPUP", "amount": 100, "note": "deposit"},
            {"type": "PAYMENT", "amount": 50, "note": "purchase"},
        ]
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": transactions})
            result = await get_transaction_history.ainvoke({}, config=ADMIN_CFG)
        assert "Deposit" in result or "Payment" in result

    @pytest.mark.asyncio
    async def test_empty_transactions(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": []})
            result = await get_transaction_history.ainvoke({}, config=ADMIN_CFG)
        assert "chưa" in result.lower() or "không" in result.lower()

    @pytest.mark.asyncio
    async def test_only_shows_max_5_transactions(self):
        transactions = [{"type": "TOPUP", "amount": i, "note": f"tx{i}"} for i in range(10)]
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": transactions})
            result = await get_transaction_history.ainvoke({}, config=ADMIN_CFG)

        assert "6. " not in result

    @pytest.mark.asyncio
    async def test_no_token_returns_auth_message(self):
        result = await get_transaction_history.ainvoke({}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower() or "đăng nhập" in result.lower()

    @pytest.mark.asyncio
    async def test_non_200_response(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(503, {})
            result = await get_transaction_history.ainvoke({}, config=ADMIN_CFG)
        assert "gián đoạn" in result.lower() or "sự cố" in result.lower()






class TestRedeemVoucher:

    @pytest.mark.asyncio
    async def test_successful_redeem(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"bonus_dl": 200}})
            result = await redeem_voucher.ainvoke({"code": "GIFT200"}, config=ADMIN_CFG)
        assert "200" in result

    @pytest.mark.asyncio
    async def test_empty_code_rejected(self):
        result = await redeem_voucher.ainvoke({"code": ""}, config=ADMIN_CFG)
        assert "không hợp lệ" in result.lower() or "invalid" in result.lower()

    @pytest.mark.asyncio
    async def test_whitespace_only_code_rejected(self):
        result = await redeem_voucher.ainvoke({"code": "   "}, config=ADMIN_CFG)
        assert "không hợp lệ" in result.lower() or "invalid" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await redeem_voucher.ainvoke({"code": "GIFT200"}, config=NO_AUTH_CFG)
        assert "đăng nhập" in result.lower() or "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_non_200_response(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(404, {})
            result = await redeem_voucher.ainvoke({"code": "BADCODE"}, config=ADMIN_CFG)
        assert "không thể" in result.lower() or "hệ thống" in result.lower()

    @pytest.mark.asyncio
    async def test_strips_whitespace_from_code(self):
        """Code is trimmed before being sent."""
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"bonus_dl": 50}})
            result = await redeem_voucher.ainvoke({"code": "  CODE  "}, config=ADMIN_CFG)

            call_kwargs = mock_req.call_args
            assert call_kwargs[1]["json"]["code"] == "CODE"






class TestGetRevenueReport:

    @pytest.mark.asyncio
    async def test_returns_revenue_on_200(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"total_revenue": 1500, "pending_withdrawal": 400}})
            result = await get_revenue_report.ainvoke({}, config=ADMIN_CFG)
        assert "1500" in result
        assert "400" in result

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await get_revenue_report.ainvoke({}, config=NO_AUTH_CFG)
        assert "đăng nhập" in result.lower() or "bảo mật" in result.lower()

    @pytest.mark.asyncio
    async def test_non_200_response(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(500, {})
            result = await get_revenue_report.ainvoke({}, config=ADMIN_CFG)
        assert "không thể" in result.lower() or "truy xuất" in result.lower()

    @pytest.mark.asyncio
    async def test_zero_revenue(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {"total_revenue": 0, "pending_withdrawal": 0}})
            result = await get_revenue_report.ainvoke({}, config=ADMIN_CFG)
        assert "0" in result






class TestGetMyDocuments:

    @pytest.mark.asyncio
    async def test_returns_document_list(self):
        docs = [
            {"title": "Research Paper", "status": "published"},
            {"title": "Draft Note", "status": "draft"},
        ]
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": docs})
            result = await get_my_documents.ainvoke({}, config=ADMIN_CFG)
        assert "Research Paper" in result
        assert "Draft Note" in result

    @pytest.mark.asyncio
    async def test_empty_document_list(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": []})
            result = await get_my_documents.ainvoke({}, config=ADMIN_CFG)
        assert "chưa" in result.lower() or "không" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await get_my_documents.ainvoke({}, config=NO_AUTH_CFG)
        assert "đăng nhập" in result.lower() or "hệ thống" in result.lower()

    @pytest.mark.asyncio
    async def test_api_error(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(503, {})
            result = await get_my_documents.ainvoke({}, config=ADMIN_CFG)
        assert "khó khăn" in result.lower() or "tải" in result.lower()






class TestGetTrashDocuments:

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await get_trash_documents.ainvoke({}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_non_admin_token_rejected(self):
        with patch("src.tools.interface._check_system_access", return_value=False):
            result = await get_trash_documents.ainvoke({}, config=ADMIN_CFG)
        assert "đặc quyền" in result.lower() or "cảnh báo" in result.lower()

    @pytest.mark.asyncio
    async def test_admin_sees_trash(self):
        trash = [{"title": "Old Doc", "deleted_at": "2024-01-01T00:00:00Z"}]
        with patch("src.tools.interface._check_system_access", return_value=True):
            with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
                mock_req.return_value = make_resp(200, {"data": trash})
                result = await get_trash_documents.ainvoke({}, config=ADMIN_CFG)
        assert "Old Doc" in result

    @pytest.mark.asyncio
    async def test_admin_empty_trash(self):
        with patch("src.tools.interface._check_system_access", return_value=True):
            with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
                mock_req.return_value = make_resp(200, {"data": []})
                result = await get_trash_documents.ainvoke({}, config=ADMIN_CFG)
        assert "không" in result.lower() or "trống" in result.lower()






class TestDeleteDocument:

    @pytest.mark.asyncio
    async def test_delete_succeeds(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {})

            with patch("src.store.database.vector_store") as mock_vs:
                mock_vs.delete_by_document = AsyncMock()
                result = await delete_document.ainvoke({"document_id": "doc-123"}, config=ADMIN_CFG)
        assert "thành công" in result.lower() or "xóa" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await delete_document.ainvoke({"document_id": "doc-123"}, config=NO_AUTH_CFG)
        assert "đăng nhập" in result.lower() or "xác nhận" in result.lower()

    @pytest.mark.asyncio
    async def test_delete_api_fails(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(500, {})
            result = await delete_document.ainvoke({"document_id": "doc-123"}, config=ADMIN_CFG)
        assert "thất bại" in result.lower() or "lỗi" in result.lower()

    @pytest.mark.asyncio
    async def test_vector_store_failure_is_non_critical(self):
        """If vector store cleanup fails, delete still reports success."""
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {})
            with patch("src.store.database.vector_store") as mock_vs:
                mock_vs.delete_by_document = AsyncMock(side_effect=Exception("VS error"))
                result = await delete_document.ainvoke({"document_id": "doc-999"}, config=ADMIN_CFG)

        assert "xóa" in result.lower() or "thành công" in result.lower()






class TestRestoreDocument:

    @pytest.mark.asyncio
    async def test_restore_succeeds(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {})
            result = await restore_document.ainvoke({"document_id": "doc-123"}, config=ADMIN_CFG)
        assert "khôi phục" in result.lower() or "thành công" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await restore_document.ainvoke({"document_id": "doc-123"}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_restore_api_fails(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(404, {})
            result = await restore_document.ainvoke({"document_id": "not-exists"}, config=ADMIN_CFG)
        assert "thất bại" in result.lower() or "quá trình" in result.lower()






class TestGetDocumentAnalytics:

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await get_document_analytics.ainvoke({"document_id": "doc-x"}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_non_admin_rejected(self):
        with patch("src.tools.interface._check_system_access", return_value=False):
            result = await get_document_analytics.ainvoke({"document_id": "doc-x"}, config=ADMIN_CFG)
        assert "đặc quyền" in result.lower() or "quyền" in result.lower()

    @pytest.mark.asyncio
    async def test_returns_analytics(self):
        with patch("src.tools.interface._check_system_access", return_value=True):
            with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
                mock_req.return_value = make_resp(200, {"data": {"readers_started": 200, "dropoff_rate": 45.2}})
                result = await get_document_analytics.ainvoke({"document_id": "doc-x"}, config=ADMIN_CFG)
        assert "200" in result
        assert "45" in result

    @pytest.mark.asyncio
    async def test_api_error(self):
        with patch("src.tools.interface._check_system_access", return_value=True):
            with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
                mock_req.return_value = make_resp(404, {})
                result = await get_document_analytics.ainvoke({"document_id": "missing"}, config=ADMIN_CFG)
        assert "lỗi" in result.lower() or "gặp" in result.lower()






class TestCreateDepositLink:

    @pytest.mark.asyncio
    async def test_returns_payment_url(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(201, {"data": {"checkout_url": "https://pay.example.com/abc"}})
            result = await create_deposit_link.ainvoke({"amount": 100000}, config=ADMIN_CFG)
        assert "https://pay.example.com/abc" in result or "nạp" in result.lower()

    @pytest.mark.asyncio
    async def test_no_checkout_url(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": {}})
            result = await create_deposit_link.ainvoke({"amount": 100000}, config=ADMIN_CFG)
        assert "không thể" in result.lower() or "khởi tạo" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await create_deposit_link.ainvoke({"amount": 50000}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower() or "đăng nhập" in result.lower()

    @pytest.mark.asyncio
    async def test_api_error(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(500, {})
            result = await create_deposit_link.ainvoke({"amount": 50000}, config=ADMIN_CFG)
        assert "lỗi" in result.lower() or "gặp" in result.lower()






class TestCreateDocument:

    @pytest.mark.asyncio
    async def test_create_json_document(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:

            mock_req.side_effect = [
                make_resp(200, {"data": {"full_name": "Test User"}}),
                make_resp(201, {"data": {"id": "new-doc-id"}}),
            ]
            result = await create_document.ainvoke({
                "title": "Test Doc",
                "description": "A test document",
                "content": '{"blocks":[{"type":"paragraph","data":{"text":"Hello"}}]}',
                "format": "json",
            }, config=ADMIN_CFG)
        assert "new-doc-id" in result or "tạo" in result.lower()

    @pytest.mark.asyncio
    async def test_create_latex_document(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": {"full_name": "Author"}}),
                make_resp(200, {"data": {"id": "latex-doc-id"}}),
            ]
            result = await create_document.ainvoke({
                "title": "LaTeX Paper",
                "description": "Math paper",
                "content": "\\documentclass{article}\\begin{document}Hello\\end{document}",
                "format": "latex",
            }, config=ADMIN_CFG)
        assert "latex-doc-id" in result or "thành công" in result.lower()

    @pytest.mark.asyncio
    async def test_create_plain_text_auto_wraps_in_json(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": {"full_name": "Writer"}}),
                make_resp(201, {"data": {"id": "plain-id"}}),
            ]
            result = await create_document.ainvoke({
                "title": "Plain Text",
                "description": "Simple content",
                "content": "This is a paragraph\n\nSecond paragraph",
                "format": "json",
            }, config=ADMIN_CFG)
        assert "plain-id" in result or "tạo" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await create_document.ainvoke({
            "title": "T", "description": "D", "content": "C", "format": "json"
        }, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_api_create_fails(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": {"full_name": "User"}}),
                make_resp(500, {}),
            ]
            result = await create_document.ainvoke({
                "title": "Bad", "description": "D", "content": "C", "format": "json"
            }, config=ADMIN_CFG)
        assert "trục trặc" in result.lower() or "thất bại" in result.lower() or "lỗi" in result.lower()






class TestReadDocument:

    @pytest.mark.asyncio
    async def test_read_json_document(self):
        doc_data = {
            "id": "doc-abc",
            "content_format": "json",
            "content": '{"blocks":[{"type":"paragraph","data":{"text":"Content here"}}]}',
        }
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": doc_data})
            result = await read_document.ainvoke({"document_id": "doc-abc"}, config=ADMIN_CFG)
        assert "tiêu chuẩn" in result.lower() or "json" in result.lower() or "Content here" in result

    @pytest.mark.asyncio
    async def test_read_latex_document(self):
        doc_data = {
            "id": "latex-doc",
            "content_format": "latex",
            "content": "\\documentclass{article}\\begin{document}Hello\\end{document}",
        }
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": doc_data})
            result = await read_document.ainvoke({"document_id": "latex-doc"}, config=ADMIN_CFG)
        assert "toán học" in result.lower() or "latex" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await read_document.ainvoke({"document_id": "x"}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_doc_not_found(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(404, {})
            result = await read_document.ainvoke({"document_id": "not-found"}, config=ADMIN_CFG)
        assert "không thể" in result.lower() or "trích xuất" in result.lower()






class TestUpdateDocument:

    @pytest.mark.asyncio
    async def test_update_content(self):
        existing_doc = {"content_format": "json", "content": "{}"}
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": existing_doc}),
                make_resp(200, {}),
            ]
            result = await update_document.ainvoke({
                "document_id": "doc-abc",
                "new_content": '{"blocks":[{"type":"paragraph","data":{"text":"Updated"}}]}',
            }, config=ADMIN_CFG)
        assert "cập nhật" in result.lower() or "thành công" in result.lower()

    @pytest.mark.asyncio
    async def test_update_title_only(self):
        existing_doc = {"content_format": "json", "content": "{}"}
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": existing_doc}),
                make_resp(200, {}),
            ]
            result = await update_document.ainvoke({
                "document_id": "doc-abc",
                "title": "New Title",
            }, config=ADMIN_CFG)
        assert "cập nhật" in result.lower() or "thành công" in result.lower()

    @pytest.mark.asyncio
    async def test_no_payload_returns_no_change_message(self):
        existing_doc = {"content_format": "json", "content": "{}"}
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": existing_doc})
            result = await update_document.ainvoke({
                "document_id": "doc-abc",
            }, config=ADMIN_CFG)
        assert "thay đổi" in result.lower() or "ghi nhận" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await update_document.ainvoke({"document_id": "doc-abc"}, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_document_not_found(self):
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(404, {})
            result = await update_document.ainvoke({
                "document_id": "missing",
                "title": "New Title",
            }, config=ADMIN_CFG)
        assert "không được phép" in result.lower() or "không còn tồn tại" in result.lower()






class TestTranslateDocument:

    @pytest.mark.asyncio
    async def test_translate_json_document(self):
        source_doc = {
            "content_format": "json",
            "content": '{"blocks":[{"type":"paragraph","data":{"text":"Xin chào"}}]}',
            "title": "Vietnamese Doc",
        }
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:

            mock_req.side_effect = [
                make_resp(200, {"data": source_doc}),
                make_resp(200, {"translation": "Hello"}),
                make_resp(201, {"data": {"id": "translated-id"}}),
            ]
            result = await translate_document.ainvoke({
                "document_id": "vn-doc",
                "target_language": "English",
            }, config=ADMIN_CFG)
        assert "translated-id" in result or "thành công" in result.lower() or "bản dịch" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_document_cannot_be_translated(self):
        source_doc = {"content_format": "json", "content": "", "title": "Empty Doc"}
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = make_resp(200, {"data": source_doc})
            result = await translate_document.ainvoke({
                "document_id": "empty-doc",
                "target_language": "English",
            }, config=ADMIN_CFG)
        assert "trống" in result.lower() or "không chứa" in result.lower()

    @pytest.mark.asyncio
    async def test_no_token(self):
        result = await translate_document.ainvoke({
            "document_id": "doc-x",
            "target_language": "English",
        }, config=NO_AUTH_CFG)
        assert "xác thực" in result.lower()

    @pytest.mark.asyncio
    async def test_translation_service_fails(self):
        source_doc = {
            "content_format": "json",
            "content": '{"blocks":[{"type":"paragraph","data":{"text":"Some text"}}]}',
            "title": "Doc",
        }
        with patch("src.tools.interface._make_api_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = [
                make_resp(200, {"data": source_doc}),
                make_resp(503, {}),
            ]
            result = await translate_document.ainvoke({
                "document_id": "vn-doc",
                "target_language": "English",
            }, config=ADMIN_CFG)
        assert "sự cố" in result.lower() or "dịch" in result.lower()






_TEST_SECRET = "test-secret-key-for-check-access"

class TestCheckSystemAccess:

    def test_valid_admin_token(self):
        import jwt
        token = jwt.encode(
            {"sub": "admin@test.com", "role": "admin"},
            _TEST_SECRET,
            algorithm="HS256",
        )
        with patch("src.core.infrastructure.configuration.settings") as mock_s:
            mock_s.SECRET_KEY = _TEST_SECRET
            result = _check_system_access(f"Bearer {token}")
        assert result is True

    def test_non_admin_role(self):
        import jwt
        token = jwt.encode(
            {"sub": "user@test.com", "role": "member"},
            _TEST_SECRET,
            algorithm="HS256",
        )
        with patch("src.core.infrastructure.configuration.settings") as mock_s:
            mock_s.SECRET_KEY = _TEST_SECRET
            result = _check_system_access(f"Bearer {token}")
        assert result is False

    def test_invalid_token(self):
        result = _check_system_access("Bearer INVALID_TOKEN")
        assert result is False

    def test_empty_token(self):
        result = _check_system_access("")
        assert result is False

    def test_no_bearer_prefix_raw_jwt_works(self):
        import jwt
        token = jwt.encode(
            {"sub": "admin@test.com", "role": "admin"},
            _TEST_SECRET,
            algorithm="HS256",
        )

        with patch("src.core.infrastructure.configuration.settings") as mock_s:
            mock_s.SECRET_KEY = _TEST_SECRET
            result = _check_system_access(token)
        assert result is True
