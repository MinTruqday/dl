import json
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from src.tools.http_client import (
    INTERNAL_API_URL,
    make_api_request,
)

@tool
async def manage_user_instructions(
    action: str, instruction: str = "", config: RunnableConfig = None
) -> str:
    """
    <module_purpose>
    Manage custom AI instructions and personal response preferences for the current user.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user asks to save a personal preference, remember a custom instruction for future chats, or view/clear saved instructions.
    - Actions supported: 'get' (view current preferences), 'set' (save/update instruction), 'clear' (reset preferences).
    CRITICAL: Requires authentication token.
    </contract>
    """
    token = config.get("configurable", {}).get("token") if config else None
    if not token:
        return json.dumps({"status": "authentication_required"})

    headers = {"Authorization": token}
    action_type = action.strip().lower()

    try:
        if action_type == "get":
            res = await make_api_request(
                "GET",
                f"{INTERNAL_API_URL}/tro-chuyen/tuy-chon-ca-nhan",
                headers=headers,
                timeout=30.0,
            )
            if res.status_code == 200:
                data = res.json().get("data", {})
                instructions = data.get("instructions", "")
                return json.dumps({
                    "status": "success",
                    "instructions": instructions,
                }, ensure_ascii=False)
            return json.dumps({"status": "instruction_retrieval_failed"})

        elif action_type == "set":
            if not instruction.strip():
                return json.dumps({"status": "instruction_required"})
            res = await make_api_request(
                "POST",
                f"{INTERNAL_API_URL}/tro-chuyen/tuy-chon-ca-nhan",
                json={"instructions": instruction.strip()},
                headers=headers,
                timeout=30.0,
            )
            if res.status_code == 200:
                return json.dumps({
                    "status": "success",
                    "instructions": instruction.strip(),
                }, ensure_ascii=False)
            return json.dumps({"status": "instruction_update_failed"})

        elif action_type == "clear":
            res = await make_api_request(
                "DELETE",
                f"{INTERNAL_API_URL}/tro-chuyen/tuy-chon-ca-nhan",
                headers=headers,
                timeout=30.0,
            )
            if res.status_code == 200:
                return json.dumps({"status": "success", "instructions": ""})
            return json.dumps({"status": "instruction_clear_failed"})

        return json.dumps({"status": "invalid_instruction_action"})
    except Exception:
        logger.exception("Failed to execute manage_user_instructions")
        return json.dumps({"status": "instruction_operation_failed"})
