import json

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from src.tools.http_client import INTERNAL_API_URL, make_api_request

@tool
async def get_user_balance(config: RunnableConfig) -> str:
    """
    <module_purpose>
    Get the current user's DocLib wallet balance in dl currency.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks about their remaining credits, balance, or how much money they have.
    CRITICAL: Requires authentication. If unauthorized, prompt the user to log in.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/so-du",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            balance = data.get("balance", 0)
            return json.dumps({"status": "success", "balance": balance})
        elif response.status_code == 401:
            return json.dumps({"status": "authentication_required"})
        return json.dumps({"status": "balance_retrieval_failed"})
    except Exception:
        logger.exception("Failed to access balance data")
        return json.dumps({"status": "balance_service_unavailable"})

@tool
async def get_transaction_history(config: RunnableConfig) -> str:
    """
    <module_purpose>
    View recent financial transaction history including deposit and payments.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks for a history of their deposits, top-ups, payments, or where their money went.
    CRITICAL: Only shows recent transactions. Requires authentication.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/vi-tien/giao-dich",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", [])
            return json.dumps(
                {"status": "success", "transactions": data[:5]},
                ensure_ascii=False,
            )
        return json.dumps({"status": "transaction_history_retrieval_failed"})
    except Exception:
        logger.exception("Failed to retrieve payment transaction history")
        return json.dumps({"status": "billing_service_unavailable"})

@tool
async def get_revenue_report(config: RunnableConfig) -> str:
    """
    <module_purpose>
    Retrieve platform revenue report for administrative review.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when an administrator asks for overall system revenue reports.
    CRITICAL: Requires admin privileges.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "admin_authorization_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "GET",
            f"{INTERNAL_API_URL}/admin/doanh-thu",
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            return json.dumps(
                {"status": "success", "total_revenue": data.get("total_revenue", 0)}
            )
        return json.dumps({"status": "revenue_report_retrieval_failed"})
    except Exception:
        logger.exception("Failed to load revenue report")
        return json.dumps({"status": "billing_service_unavailable"})
