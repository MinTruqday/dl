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
async def redeem_voucher(code: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Redeem a gift voucher code to add funds to the account.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly provides a voucher code or promo code and asks to redeem it.
    CRITICAL: The code must be a non-empty string.
    </contract>
    """
    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    if not code or not code.strip():
        return json.dumps({"status": "voucher_code_required"})
    headers = {"Authorization": token}
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/vi-tien/ma-qua-tang/su-dung",
            json={"code": code.strip()},
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            res_data = response.json().get("data", {})
            bonus = res_data.get("bonus_dl", 0)
            return json.dumps({"status": "success", "credited_amount": bonus})
        return json.dumps({"status": "voucher_redemption_failed"})
    except Exception:
        logger.exception("Failed to process reward redemption request")
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

@tool
async def transfer_user_funds(recipient_identifier: str, amount: int, note: str = "", config: RunnableConfig = None) -> str:
    """
    <module_purpose>
    Transfer dl credits from current user's wallet to another user (Peer-to-Peer transfer).
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user requests to send, transfer, or give money/credits to another user.
    CRITICAL: Requires recipient_identifier (email, user_id, or slug) and amount > 0.
    </contract>
    """
    token = config.get("configurable", {}).get("token") if config else None
    if not token:
        return json.dumps({"status": "authentication_required"})
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        response = await make_api_request(
            "POST",
            f"{INTERNAL_API_URL}/vi-tien/chuyen-tien",
            json_data={
                "recipient_identifier": recipient_identifier,
                "amount": amount,
                "note": note
            },
            headers=headers,
            timeout=30.0,
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            recipient_name = data.get("recipient", {}).get("name", recipient_identifier)
            remaining = data.get("remaining_balance", 0)
            return json.dumps(
                {
                    "status": "success",
                    "amount": amount,
                    "recipient": recipient_name,
                    "remaining_balance": remaining,
                },
                ensure_ascii=False,
            )
        else:
            return json.dumps({"status": "fund_transfer_failed"})
    except Exception:
        logger.exception("Failed to execute P2P fund transfer")
        return json.dumps({"status": "billing_service_unavailable"})
