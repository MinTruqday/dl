import asyncio
import os
import tempfile

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.prompt_registry import PromptType, prompt_registry

from core.infrastructure.app_config import settings


class CodeExecution:
    def __init__(self):
        pass

    async def execute(self, task_desc: str) -> str:
        logger.info("Processing task")

        try:
            from src.agents.task_planning import llm

            system_prompt = (
                prompt_registry.get(PromptType.CODE_INTERPRETER_SYSTEM) + "\\n"
                "OBJECTIVE: Generate pure, executable Python code to fulfill the user's task.\n"
                "OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.\n\n"
                "RULES:\n"
                "- Output ONLY valid Python code wrapped in ```python code_here ``` tags.\n"
                "- Do NOT include any conversational text or explanations.\n"
                "- Use the `print` function to output results.\n"
                "- Assume a standard Python 3.9 environment with standard libraries only"
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_desc),
            ]
            response = await llm.ainvoke(messages)
            content = response.content.strip()

            import re

            match = re.search(r"```[pP]ython(.*?)```", content, re.DOTALL)
            if match:
                code = match.group(1).strip()
            else:
                match = re.search(r"```(.*?)```", content, re.DOTALL)
                if match:
                    code = match.group(1).strip()
                else:
                    code = content.strip()

            def write_temp_script(content):
                import tempfile

                f = tempfile.NamedTemporaryFile(
                    suffix=".py", delete=False, mode="w", encoding="utf-8"
                )
                f.write(content)
                f.close()
                return f.name

            script_path = await asyncio.to_thread(write_temp_script, code)

            try:
                docker_cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{script_path}:/app/script.py:ro",
                    "--network",
                    "none",
                    "--memory",
                    "128m",
                    "--memory-swap",
                    "128m",
                    "--cpus",
                    "0.5",
                    "--pids-limit",
                    "64",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:size=50m,noexec,nosuid",
                    "--cap-drop",
                    "ALL",
                    "python:3.9-slim",
                    "python",
                    "/app/script.py",
                ]

                proc = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout=settings.DEFAULT_HTTP_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.communicate()
                    return "Execution exceeded time limit and terminated"

                MAX_OUTPUT = 512 * 1024
                if proc.returncode == 0:
                    out = stdout[:MAX_OUTPUT]
                    final_res = f"The execution completed with the following output\n{out.decode(errors='replace')}\n"
                    if len(stdout) > MAX_OUTPUT:
                        final_res += "\nThe output was truncated due to exceeding the maximum allowed size limit"
                else:
                    err = stderr[:MAX_OUTPUT]
                    final_res = f"The execution encountered the following issues\n{err.decode(errors='replace')}\n"

            finally:

                def remove_if_exists(path):
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass

                await asyncio.to_thread(remove_if_exists, script_path)

            if not final_res.strip():
                final_res = "The execution process completed successfully without producing any output"

            return final_res
        except Exception:
            logger.error("Internal execution error")
            return "Execution error, please retry"


code_interpreter = CodeExecution()
