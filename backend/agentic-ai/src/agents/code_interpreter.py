import os
import tempfile
import asyncio
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.prompt_registry import prompt_registry, PromptType


class CodeInterpreter:
    def __init__(self):
        pass

    async def execute(self, task_desc: str) -> str:
        logger.info(f"CodeInterpreter: Processing task (Docker Sandbox): {task_desc}")
        
        try:
            from src.agents.planning import llm
            
            system_prompt = (
                prompt_registry.get(PromptType.CODE_INTERPRETER_SYSTEM) + "\\n"
                "OBJECTIVE: Generate pure, executable Python code to fulfill the user's task.\n"
                "OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.\n\n"
                "RULES:\n"
                "- Output ONLY valid Python code wrapped in ```python code_here ``` tags.\n"
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

            def write_temp_script(content):
                import tempfile
                f = tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8')
                f.write(content)
                f.close()
                return f.name
                
            script_path = await asyncio.to_thread(write_temp_script, code)
                
            try:
                docker_cmd = [
                    "python", script_path
                ]
                
                proc = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.communicate()
                    return "Security error: Code execution exceeded the allowed time limit (timeout 15s)."
                
                if proc.returncode == 0:
                    final_res = f"Execution output:\n{stdout.decode()}\n"
                else:
                    final_res = f"Execution error:\n{stderr.decode()}\n"
                    
            finally:
                def remove_if_exists(path):
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                await asyncio.to_thread(remove_if_exists, script_path)
                    
            if not final_res.strip():
                final_res = "Code executed successfully (no output)."
                
            return final_res
        except Exception as e:
            logger.error(f"CodeInterpreter: Execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

code_interpreter = CodeInterpreter()
