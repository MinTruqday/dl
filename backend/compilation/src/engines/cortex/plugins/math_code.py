from typing import Any, Dict
from src.engines.cortex.plugins.base import BaseBlockTranslator

class MathTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "")
        args = block.get("args", {})
        if "inline" in args:
            return f"${content.strip()}$"
        elif "label" in args:
            label = args.get("label")
            return f"\\begin{{equation}}\\label{{{label}}}\n{content.strip()}\n\\end{{equation}}\n\n"
        else:
            return f"\\[\n{content.strip()}\n\\]\n\n"

class CodeTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "")
        args = block.get("args", {})
        lang = args.get("lang")
        if not lang:
            for k, v in args.items():
                if v is True:
                    lang = k
                    break
        if lang:
            return f"\\begin{{lstlisting}}[language={lang}]\n{content}\n\\end{{lstlisting}}\n\n"
        else:
            return f"\\begin{{lstlisting}}\n{content}\n\\end{{lstlisting}}\n\n"
