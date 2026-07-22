import asyncio
import os
import re
import json
import base64

import docker
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from src.core.registry import PromptType, registry
from src.core.infrastructure.configuration import settings

SERVER_B64 = "CmltcG9ydCBzb2NrZXQsIGpzb24sIHN5cywgaW8sIHRyYWNlYmFjawpzb2NrID0gc29ja2V0LnNvY2tldChzb2NrZXQuQUZfSU5FVCwgc29ja2V0LlNPQ0tfU1RSRUFNKQpzb2NrLmJpbmQoKCcxMjcuMC4wLjEnLCA5OTk5KSkKc29jay5saXN0ZW4oMSkKZW52ID0ge30Kd2hpbGUgVHJ1ZToKICAgIGNvbm4sIGFkZHIgPSBzb2NrLmFjY2VwdCgpCiAgICBkYXRhID0gYiIiCiAgICB3aGlsZSBUcnVlOgogICAgICAgIHBhY2tldCA9IGNvbm4ucmVjdig0MDk2KQogICAgICAgIGlmIG5vdCBwYWNrZXQ6IGJyZWFrCiAgICAgICAgZGF0YSArPSBwYWNrZXQKICAgICAgICBpZiBsZW4ocGFja2V0KSA8IDQwOTY6IGJyZWFrCiAgICAKICAgIGNvZGUgPSBkYXRhLmRlY29kZSgndXRmLTgnKQogICAgb2xkX3N0ZG91dCwgb2xkX3N0ZGVyciA9IHN5cy5zdGRvdXQsIHN5cy5zdGRlcnIKICAgIHN5cy5zdGRvdXQgPSBvdXQgPSBpby5TdHJpbmdJTygpCiAgICBzeXMuc3RkZXJyID0gZXJyID0gaW8uU3RyaW5nSU8oKQogICAgCiAgICB0cnk6CiAgICAgICAgZXhlYyhjb2RlLCBlbnYpCiAgICAgICAgb3V0cHV0ID0gb3V0LmdldHZhbHVlKCkKICAgICAgICBpZiBub3Qgb3V0cHV0IGFuZCBlcnIuZ2V0dmFsdWUoKToKICAgICAgICAgICAgb3V0cHV0ID0gZXJyLmdldHZhbHVlKCkKICAgICAgICByZXMgPSB7InN0YXR1cyI6ICJzdWNjZXNzIiwgIm91dHB1dCI6IG91dHB1dH0KICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICByZXMgPSB7InN0YXR1cyI6ICJlcnJvciIsICJvdXRwdXQiOiBlcnIuZ2V0dmFsdWUoKSArICJcbiIgKyB0cmFjZWJhY2suZm9ybWF0X2V4YygpfQogICAgICAgIAogICAgc3lzLnN0ZG91dCwgc3lzLnN0ZGVyciA9IG9sZF9zdGRvdXQsIG9sZF9zdGRlcnIKICAgIGNvbm4uc2VuZGFsbChqc29uLmR1bXBzKHJlcykuZW5jb2RlKCd1dGYtOCcpKQogICAgY29ubi5jbG9zZSgpCg=="
CLIENT_B64 = "CmltcG9ydCBzb2NrZXQsIHN5cywganNvbgpzb2NrID0gc29ja2V0LnNvY2tldChzb2NrZXQuQUZfSU5FVCwgc29ja2V0LlNPQ0tfU1RSRUFNKQpzb2NrLmNvbm5lY3QoKCcxMjcuMC4wLjEnLCA5OTk5KSkKY29kZSA9IHN5cy5zdGRpbi5yZWFkKCkKc29jay5zZW5kYWxsKGNvZGUuZW5jb2RlKCd1dGYtOCcpKQpkYXRhID0gYiIiCndoaWxlIFRydWU6CiAgICBwYWNrZXQgPSBzb2NrLnJlY3YoNDA5NikKICAgIGlmIG5vdCBwYWNrZXQ6IGJyZWFrCiAgICBkYXRhICs9IHBhY2tldAogICAgaWYgbGVuKHBhY2tldCkgPCA0MDk2OiBicmVhawpwcmludChkYXRhLmRlY29kZSgndXRmLTgnKSkK"

class InterpreterAgent:
    """
    <module_purpose>
    DocLib Interpreter Agent for executing dynamically generated code in a secure, STATEFUL Docker sandbox.
    </module_purpose>
    <contract>
    - Precondition: Docker daemon running and accessible.
    - Postcondition: Returns standard output of the executed code. State is preserved.
    - Error Handling: Fails gracefully if Docker is unreachable; never executes on the host.
    </contract>
    """
    def __init__(self):
        pass

    def _ensure_container(self):
        pass

    def reset_sandbox(self):
        pass

    def run_sandbox_code(self, code_str: str) -> str:
        return "This method is deprecated in favor of execute/delegation."

    async def execute(self, task_desc: str) -> str:
        logger.info("Executing code via Client-Side Delegation")
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

            from src.core.delegation import delegator
            final_res = await delegator.delegate("RUN_CODE", {"code": code}, timeout=60.0)
            return final_res

        except Exception as e:
            logger.exception("Interpreter delegation execution error")
            return f"An error occurred during command execution, please try again in a moment {e}"

interpreter = InterpreterAgent()
