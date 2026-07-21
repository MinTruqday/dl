from typing import Any, Dict
from src.engines.cortex.plugins.base import BaseBlockTranslator

class ContainerTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        b_type = block.get("type")
        children = block.get("children", [])
        children_latex = await ast_to_latex_fn(children, temp_dir)
        return f"\\begin{{cortex{b_type}}}\n{children_latex.strip()}\n\\end{{cortex{b_type}}}\n\n"
