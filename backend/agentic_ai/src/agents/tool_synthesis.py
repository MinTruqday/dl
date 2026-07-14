import hashlib
import types
from typing import Callable, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.core.registry import PromptType, registry


class ToolSynthesizer:
    """
    <module_purpose>
    <purpose>Synthesizes new Python tool functions on-the-fly when no existing tool can satisfy a task.</purpose>
    <metis_behavior>Uses the LLM to generate a focused Python function, validates it in a restricted sandbox before registration, and caches it for the session lifetime.</metis_behavior>
    </module_purpose>
    """

    def __init__(self, llm):
        self.llm = llm
        self._synthesized_cache: dict[str, Callable] = {}

    def _cache_key(self, task: str) -> str:
        return hashlib.sha256(task.encode()).hexdigest()[:16]

    async def create_tool(self, task: str) -> Optional[Callable]:
        cache_key = self._cache_key(task)
        if cache_key in self._synthesized_cache:
            logger.info("Tool synthesis cache hit")
            return self._synthesized_cache[cache_key]

        logger.info("Tool synthesis started for new task requirement")
        system_prompt = (
            "You are a Python tool generator. "
            "Write a single, self-contained Python function named `synthesized_tool` that fulfills the task described. "
            "The function must accept a single string argument `input_data` and return a string result. "
            "Output ONLY the function definition code. No imports outside the function body. No explanations."
        )
        human_msg = f"Task requirement: {task}"

        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg)]
            response = await self.llm.ainvoke(messages)
            code = response.content.strip()

            import re
            match = re.search(r"```python\s*\n(.*?)```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()

            func = self._safe_compile(code)
            if func is None:
                return None

            self._synthesized_cache[cache_key] = func
            logger.info("Tool synthesis completed and registered successfully")
            return func

        except Exception:
            logger.exception("Tool synthesis failed")
            return None

    def _safe_compile(self, code: str) -> Optional[Callable]:
        try:
            from RestrictedPython import compile_restricted, safe_globals

            byte_code = compile_restricted(code, "<tool_synthesis>", "exec")
            local_ns: dict = {}
            exec(byte_code, safe_globals, local_ns)  # noqa: S102

            func = local_ns.get("synthesized_tool")
            if not callable(func):
                logger.warning("Tool synthesis produced no callable function")
                return None
            return func

        except ImportError:
            logger.warning("RestrictedPython not available, using standard compile with restricted builtins")
            return self._standard_compile(code)
        except Exception:
            logger.exception("Restricted compilation failed")
            return None

    def _standard_compile(self, code: str) -> Optional[Callable]:
        ALLOWED_BUILTINS = {"len", "str", "int", "float", "list", "dict", "set", "range", "enumerate", "zip", "map", "filter", "sorted", "reversed", "min", "max", "sum", "abs", "round", "print"}
        restricted_globals = {
            "__builtins__": {k: v for k, v in __builtins__.items() if k in ALLOWED_BUILTINS}
            if isinstance(__builtins__, dict)
            else {k: getattr(__builtins__, k) for k in ALLOWED_BUILTINS if hasattr(__builtins__, k)},
        }
        try:
            local_ns: dict = {}
            exec(compile(code, "<tool_synthesis>", "exec"), restricted_globals, local_ns)  # noqa: S102
            func = local_ns.get("synthesized_tool")
            return func if callable(func) else None
        except Exception:
            logger.exception("Standard restricted compilation failed")
            return None
