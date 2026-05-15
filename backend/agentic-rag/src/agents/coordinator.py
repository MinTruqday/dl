from loguru import logger
from src.core.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.agents.search_engine import search_engine_agent
from src.agents.internal_api import internal_api_agent
from src.agents.draft_generator import draft_generator_agent

class CoordinatorAgent:
    def __init__(self):
        pass

    async def execute_plan(self, query: str, context: str, user_id: str):
        logger.info("Coordinator: Bắt đầu xử lý luồng Agentic AI")
        
        yield {"type": "status", "node": "Lập kế hoạch phân rã tác vụ (Brain)"}
        steps = await brain.create_plan(query, context)
        
        yield {"type": "plan", "steps": steps}
        
        consolidated_results = []
        for index, step in enumerate(steps):
            agent_name = "Unknown"
            if "CodeInterpreter" in step:
                agent_name = "CodeInterpreter"
            elif "SearchEngine" in step:
                agent_name = "SearchEngine"
            elif "InternalAPI" in step:
                agent_name = "InternalAPI"
            elif "DraftGenerator" in step:
                agent_name = "DraftGenerator"
            
            yield {"type": "status", "node": f"Đang thực thi: {step}"}
            
            try:
                if agent_name == "CodeInterpreter":
                    result = await code_interpreter_agent.execute(f"print('Processing {step}')")
                elif agent_name == "SearchEngine":
                    result = await search_engine_agent.execute(query)
                elif agent_name == "InternalAPI":
                    result = await internal_api_agent.execute(step, {}, user_id)
                elif agent_name == "DraftGenerator":
                    result = await draft_generator_agent.execute(step)
                else:
                    result = await internal_api_agent.execute(step, {}, user_id)
                    
                consolidated_results.append(f"Kết quả bước {index+1} ({agent_name}):\n{result}")
                yield {"type": "tool_result", "agent": agent_name, "content": result[:500] + ("..." if len(result) > 500 else "")}
            
            except Exception as e:
                logger.error(f"Coordinator: Lỗi ở bước {step}: {e}")
                error_msg = f"Lỗi thực thi bước {index+1}: Hệ thống đang bảo trì dữ liệu."
                consolidated_results.append(error_msg)
                yield {"type": "error", "message": error_msg}

        yield {"type": "status", "node": "Tổng hợp kết quả (Aggregator)"}
        
        final_prompt = f"Bạn là một Aggregator. Hãy tổng hợp các dữ liệu sau để trả lời yêu cầu ban đầu một cách tự nhiên, lịch sự (KHÔNG dùng emoji, dùng tiếng Việt chuẩn).\nYêu cầu: {query}\n\nDữ liệu:\n" + "\n\n".join(consolidated_results)
        
        try:
            from src.core.brain import llm
            from langchain_core.messages import HumanMessage
            
            final_response = await llm.ainvoke([HumanMessage(content=final_prompt)])
            yield {"type": "message", "chunk": final_response.content.strip()}
        except Exception as e:
            logger.error(f"Coordinator: Lỗi tổng hợp: {e}")
            yield {"type": "message", "chunk": "Hệ thống gặp sự cố trong quá trình tổng hợp dữ liệu."}

coordinator = CoordinatorAgent()
