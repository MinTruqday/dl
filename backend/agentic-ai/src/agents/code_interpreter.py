import os
import tempfile
import subprocess
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

class CodeInterpreterAgent:
    def __init__(self):
        pass

    async def execute(self, task_desc: str) -> str:
        logger.info(f"CodeInterpreter: Processing task (Docker Sandbox): {task_desc}")
        
        try:
            from src.core.brain import llm
            
            system_prompt = (
                "Bạn là một trợ lý phân tích dữ liệu và lập trình Python. Hãy viết mã Python để hoàn thành yêu cầu sau.\n"
                "Trả về DUY NHẤT mã Python nằm trong thẻ ```python ... ```, KHÔNG GIẢI THÍCH THÊM.\n"
                "Sử dụng lệnh `print` để xuất kết quả. Môi trường chỉ có Python tiêu chuẩn (standard library)."
            )
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

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                script_path = f.name
                
            try:
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{script_path}:/app/script.py",
                    "--memory=128m",
                    "--cpus=0.5",
                    "--network=none",
                    "python:3.9-slim",
                    "python", "/app/script.py"
                ]
                
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.returncode == 0:
                    final_res = f"Kết quả in ra:\n{result.stdout}\n"
                else:
                    final_res = f"Lỗi thực thi mã:\n{result.stderr}\n"
                    
            except subprocess.TimeoutExpired:
                final_res = "Lỗi bảo mật: Mã thực thi vượt quá thời gian quy định (Timeout 15s)."
            finally:
                if os.path.exists(script_path):
                    os.remove(script_path)
                    
            if not final_res.strip():
                final_res = "Mã đã được thực thi thành công (Không có output)."
                
            return final_res
        except Exception as e:
            logger.error(f"CodeInterpreter: Execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

code_interpreter_agent = CodeInterpreterAgent()

