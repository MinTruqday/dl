from typing import Any, Dict
from src.engines.cortex.plugins.base import BaseBlockTranslator

class ParagraphTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "")
        return escape_fn(content) + "\n\n"

class HeadingTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        b_type = block.get("type")
        content = block.get("content", "")
        escaped = escape_fn(content)
        if b_type == "h1":
            return f"\\section{{{escaped}}}\n\n"
        elif b_type == "h2":
            return f"\\subsection{{{escaped}}}\n\n"
        elif b_type == "h3":
            return f"\\subsubsection{{{escaped}}}\n\n"
        return ""

class RawTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "")
        return content + "\n\n"
