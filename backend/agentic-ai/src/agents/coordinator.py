from loguru import logger
from src.core.brain import brain
from src.agents.code_interpreter import code_interpreter_agent
from src.tools.search_engine import search_engine_agent
from src.agents.internal_api import internal_api_agent
from src.agents.draft_generator import draft_generator_agent
from src.agents.rag_agent import rag_agent

class CoordinatorAgent:
    def __init__(self):
        pass

    async def execute_plan(self, req):
        logger.info("Coordinator: Starting Agentic AI execution flow")
        
        yield {"type": "status", "node": "Lập kế hoạch phân rã tác vụ (Brain)"}
        steps = await brain.create_plan(req)
        
        yield {"type": "plan", "steps": steps}
        
        consolidated_results = []
        for index, step_dict in enumerate(steps):
            if not isinstance(step_dict, dict):
                continue
                
            agent_name = step_dict.get("agent", "ActionAgent")
            task_desc = step_dict.get("task", "Xử lý trực tiếp yêu cầu")
            
            yield {"type": "status", "node": f"Đang thực thi: {task_desc}"}
            
            try:
                if agent_name == "CodeInterpreter":
                    result = await code_interpreter_agent.execute(task_desc)
                elif agent_name == "SearchEngine":
                    result = await search_engine_agent.execute(task_desc)
                elif agent_name == "ActionAgent" or agent_name == "InternalAPI":
                    result = await internal_api_agent.execute(task_desc, {}, req.user_id)
                elif agent_name == "DraftGenerator":
                    result = await draft_generator_agent.execute(task_desc)
                elif agent_name == "RAGAgent":
                    result = await rag_agent.execute(req)
                else:
                    result = await internal_api_agent.execute(task_desc, {}, req.user_id)
                    
                consolidated_results.append(f"Kết quả bước {index+1} ({agent_name}):\n{result}")
                yield {"type": "tool_result", "agent": agent_name, "content": f"Đã xử lý xong tác vụ với {len(result)} ký tự dữ liệu."}
            
            except Exception as e:
                logger.error(f"Coordinator: Step execution failed for task '{task_desc}': {e}")
                error_msg = "Hệ thống đang gặp sự cố, vui lòng thử lại sau."
                consolidated_results.append(error_msg)
                yield {"type": "error", "message": error_msg}

        yield {"type": "status", "node": "Tổng hợp kết quả (Aggregator)"}
        
        from src.agents.aggregator import aggregator_agent
        final_answer = await aggregator_agent.aggregate(req.query, consolidated_results)
        
        yield {"type": "message", "chunk": final_answer}

coordinator = CoordinatorAgent()
