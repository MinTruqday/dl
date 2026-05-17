import httpx
from loguru import logger
from src.core.config import settings
from src.agents.action import auth_token_var
from langchain_core.messages import HumanMessage
from src.agents.action import action_agent_app

class InternalAPIAgent:
    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL

    async def execute(self, action: str, params: dict, user_id: str) -> str:
        logger.info(f"InternalAPI: Executing action '{action}' for user {user_id}")
        
        token = auth_token_var.get()
        if not token and action != "public_query":
            return "Lỗi xác thực: Vui lòng đăng nhập để thực hiện thao tác với hệ thống."
            
        try:
            messages = [HumanMessage(content=f"Truy vấn từ ID người dùng <{user_id}>. Yêu cầu: {action}. Tham số: {params}")]
            config = {"configurable": {"thread_id": f"internal_{user_id}"}}
            
            res = await action_agent_app.ainvoke({"messages": messages}, config=config)
            return res["messages"][-1].content
        except Exception as e:
            logger.error(f"InternalAPI: Task execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

internal_api_agent = InternalAPIAgent()
