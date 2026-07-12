import asyncio
import os
import re

import docker
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.registry import PromptType, registry

from src.core.infrastructure.configuration import settings

class InterpreterAgent:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Docker daemon initialization failed with error {e}")
            self.docker_client = None

    async def execute(self, task_desc: str) -> str:
        logger.info("Initializing ephemeral sandbox for code execution")
        try:
            from src.agents.planning import llm

            system_prompt = registry.get(PromptType.CODE_INTERPRETER_SYSTEM)
            
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_desc),
            ])
            
            content = response.content.strip()
            match = re.search(r"```[pP]ython(.*?)```", content, re.DOTALL)
            code = match.group(1).strip() if match else content.replace("```", "").strip()

            def _run_sandbox(code_str: str) -> str:
                if not self.docker_client:
                    return "The execution environment is currently unavailable"
                try:
                    container = self.docker_client.containers.run(
                        "python:3.11-slim",
                        command=["python", "-c", code_str],
                        mem_limit="128m",
                        nano_cpus=1000000000,
                        network_mode="none",
                        detach=True,
                        remove=False
                    )
                    container.wait(timeout=10)
                    logs = container.logs().decode('utf-8', errors='replace')
                    container.remove(force=True)
                    return f"Thực thi mã thành công. Output:\n{logs[:10240]}"
                except Exception as ex:
                    return f"The execution process was terminated due to an error or timeout {ex}"

            final_res = await asyncio.to_thread(_run_sandbox, code)
            return final_res

        except Exception as e:
            logger.exception("Interpreter system execution error")
            return f"An error occurred during command execution, please try again in a moment {e}"

interpreter = InterpreterAgent()
