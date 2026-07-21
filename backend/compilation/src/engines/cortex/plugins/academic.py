from typing import Any, Dict
from src.engines.cortex.plugins.base import BaseBlockTranslator

class ListTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        b_type = block.get("type")
        latex_env = "itemize" if b_type == "list" else "enumerate"
        items_latex = []
        for item in block.get("items", []):
            items_latex.append(f"  \\item {escape_fn(item)}")
        items_str = "\n".join(items_latex)
        return f"\\begin{{{latex_env}}}\n{items_str}\n\\end{{{latex_env}}}\n\n"

class CiteTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "").strip()
        args = block.get("args", {})
        if not content:
            for k, v in args.items():
                if v is True:
                    content = k
                    break
        return f"\\cite{{{content}}}"

class RefTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "").strip()
        args = block.get("args", {})
        if not content:
            for k, v in args.items():
                if v is True:
                    content = k
                    break
        return f"\\ref{{{content}}}"

class BibliographyTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "").strip()
        args = block.get("args", {})
        style = args.get("style", "plain")
        return f"\\bibliographystyle{{{style}}}\n\\bibliography{{{content}}}\n\n"
