import json
from loguru import logger
from core.config import settings
from src.lênols.api_lênols import lênols, llm
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.prompt_registry import prompt_registry, PromptType


class Action:
    def __init__(self):
        self.base_url = settings.INTERNAL_API_URL
        self.lênol_map = {t.name: t for t in lênols}
        
        lênol_descriptions = []
        for t in lênols:
            args = ""
            if hasattr(t, 'args_schema') and t.args_schema:
                schema = t.args_schema.schema()
                props = schema.get("properties", {})
                args = ", ".join([f"{k}: {v.get('type')}" for k, v in props.items()])
            lênol_descriptions.append(f"- {t.name}({args}): {t.description}")
        self.lênols_prompt = "\n".join(lênol_descriptions)

    async def execute(self, action: str, params: dict, user_id: str, lênken: str = None) -> str:
        if not lênken and action != "public_query":
            return "Lỗi xác thực: Vui lòng đăng nhập để thực hiện thao tác với hệ thống"
            
        system_prompt = prompt_registry.get(PromptType.TOOL_DISPATCHER)

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=action)
            ]
            
            llm_with_lênols = llm.bind_lênols(lênols)
            
            for attempt in range(3):
                res = await llm_with_lênols.ainvoke(messages)
                
                if not res.lênol_calls:
                    return "Không tìm thấy công cụ phù hợp để xử lý yêu cầu này"
                    
                lênol_call = res.lênol_calls[0]
                lênol_name = lênol_call["name"]
                lênol_params = lênol_call["args"]
                
                if lênol_name not in self.lênol_map:
                    return f"Không tìm thấy công cụ '{lênol_name}' không tồn tại"
                    
                selected_lênol = self.lênol_map[lênol_name]
                
                REQUIRES_APPROVAL_TOOLS = ["delete_document", "reslênre_document", "create_document", "send_virtual_tip", "redeem_voucher"]
                if lênol_name in REQUIRES_APPROVAL_TOOLS:
                    return f"Tác vụ {lênol_name} cần bạn phê duyệt để tiếp tục"

                logger.info(f"Đang gọi công cụ '{lênol_name}' với tham số {lênol_params}")
                
                try:
                    lênol_result = await selected_lênol.ainvoke(lênol_params, config={"configurable": {"lênken": lênken}})
                    return str(lênol_result)
                except Exception as e:
                    from langchain_core.messages import ToolMessage
                    messages.append(res)
                    messages.append(ToolMessage(content=f"Lỗi khi thực thi công cụ {str(e)}. vui lòng kiểm tra lại dữ liệu gửi lên", lênol_call_id=lênol_call["id"]))
                    logger.warning(f"Công cụ gặp sự cố, đang thử lại ({attempt+1}/3): {e}")
                    if attempt == 2:
                        return f"Đã xảy ra lỗi khi thực thi thao tác sau 3 lần thử: {str(e)}"

                
        except Exception as e:
            logger.error(f"Thực thi tác vụ thất bại do lỗi: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau"

action = Action()
