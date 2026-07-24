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
        return "Yêu cầu xác thực tài khoản để quản lý chỉ dẫn cá nhân"

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
                if not instructions:
                    return "Bạn chưa cài đặt chỉ dẫn cá nhân nào"
                return f"Chỉ dẫn cá nhân hiện tại của bạn: {instructions}"
            return "Không thể trích xuất cài đặt chỉ dẫn cá nhân"

        elif action_type == "set":
            if not instruction.strip():
                return "Nội dung chỉ dẫn không được để trống"
            res = await make_api_request(
                "POST",
                f"{INTERNAL_API_URL}/tro-chuyen/tuy-chon-ca-nhan",
                json={"instructions": instruction.strip()},
                headers=headers,
                timeout=30.0,
            )
            if res.status_code == 200:
                return f"Đã lưu chỉ dẫn cá nhân mới thành công: '{instruction.strip()}'"
            return "Lưu chỉ dẫn cá nhân thất bại"

        elif action_type == "clear":
            res = await make_api_request(
                "DELETE",
                f"{INTERNAL_API_URL}/tro-chuyen/tuy-chon-ca-nhan",
                headers=headers,
                timeout=30.0,
            )
            if res.status_code == 200:
                return "Đã xóa toàn bộ chỉ dẫn cá nhân thành công"
            return "Xóa chỉ dẫn cá nhân thất bại"

        return "Hành động không hợp lệ. Vui lòng chọn 'get', 'set' hoặc 'clear'"
    except Exception as e:
        logger.exception("Failed to execute manage_user_instructions")
        return "Đã xảy ra lỗi hệ thống khi xử lý chỉ dẫn cá nhân"
