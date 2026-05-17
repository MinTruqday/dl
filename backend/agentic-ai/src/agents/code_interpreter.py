import io
import contextlib
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

class CodeInterpreterAgent:
    def __init__(self):
        pass

    async def execute(self, task_desc: str) -> str:
        logger.info(f"CodeInterpreter: Processing task: {task_desc}")
        
        try:
            from src.core.brain import llm
            
            system_prompt = "Bạn là một trợ lý lập trình Python. Hãy viết mã Python để hoàn thành yêu cầu sau. Trả về DUY NHẤT mã Python nằm trong thẻ ```python ... ```, KHÔNG GIẢI THÍCH THÊM."
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_desc)
            ]
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code = content.split("```")[1].strip()
            else:
                code = content.strip()
                
            forbidden = ["os.system", "subprocess", "rm -rf", "shutil.rmtree", "exit()", "sys.exit", "import os", "import subprocess"]
            for f in forbidden:
                if f in code:
                    return f"Lỗi bảo mật: Mã nguồn chứa lệnh không được phép '{f}'."

            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                local_env = {}
                global_env = {"__builtins__": __builtins__}
                exec(code, global_env, local_env)
                
            output = output_buffer.getvalue()
            return f"Kết quả thực thi mã:\n{output}" if output else "Mã đã được thực thi thành công (Không có output)."
        except Exception as e:
            logger.error(f"CodeInterpreter: Code generation or execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

code_interpreter_agent = CodeInterpreterAgent()
