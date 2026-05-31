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
                "SYSTEM IDENTITY: DocLib Core System - Python Execution Engine.\n"
                "OBJECTIVE: Generate pure, executable Python code to fulfill the user's task.\n"
                "OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.\n\n"
                "RULES:\n"
                "- Output ONLY valid Python code wrapped in ```python ... ``` tags.\n"
                "- Do NOT include any conversational text or explanations.\n"
                "- Use the `print` function to output results.\n"
                "- Assume a standard Python 3.9 environment with standard libraries only."
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

