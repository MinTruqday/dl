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
        return "High security operation, please log in to your account and try again"
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
            return f"Your current account balance is {balance} credits"
        elif response.status_code == 401:
            return "Your session has expired. Please log in again"
        raise Exception("Failed to load account balance")
    except Exception as e:
        logger.exception("Failed to access balance data")
        raise Exception(f"An unexpected error occurred, please try again {e}")

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
        return "Please authenticate your account to view transaction history details"
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
            if not data:
                return "No recent payment transactions recorded"
            history_text = ""
            for i, tx in enumerate(data[:5]):
                tx_type = "Deposit" if tx.get("type") == "TOPUP" else "Payment"
                amount = tx.get("amount", 0)
                note = tx.get("note", "No content")
                history_text += f"{i+1} {tx_type} transaction of {amount} credits with note {note}\n"
            return f"Here is your recent transaction history:\n{history_text}"
        return "System is experiencing issues retrieving your payment transaction history"
    except Exception as e:
        logger.exception("Failed to retrieve payment transaction history")
        raise Exception(f"An unexpected error occurred, please try again {e}")

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
        return "Valid account login is required to use a gift voucher"
    if not code or not code.strip():
        return "This promo code is invalid or has already been used"
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
            return f"Gift voucher redeemed successfully. Your account has been credited with {bonus} credits"
        return "The system cannot process the gift voucher redemption request at this time"
    except Exception as e:
        logger.exception("Failed to process reward redemption request")
        raise Exception(f"An unexpected error occurred, please try again {e}")

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
        return "Admin authorization required to access revenue reports"
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
            return f"Platform revenue report: Total revenue is {data.get('total_revenue', 0)} dl"
        return "Unable to load system revenue report"
    except Exception as e:
        logger.exception("Failed to load revenue report")
        raise Exception(f"An unexpected error occurred {e}")

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
        return "Authentication required to perform P2P fund transfer"
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
            return f"Successfully transferred {amount} dl to {recipient_name}. Remaining balance: {remaining} dl"
        else:
            detail = response.json().get("detail") or "Fund transfer failed"
            return f"Transfer failed: {detail}"
    except Exception as e:
        logger.exception("Failed to execute P2P fund transfer")
        return f"Transfer failed due to system error: {e}"

