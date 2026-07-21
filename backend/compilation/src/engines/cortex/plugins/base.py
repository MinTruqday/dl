from typing import Any, Dict

class BaseBlockTranslator:
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        """Translate a single AST block to LaTeX code.
        
        Args:
            block: The AST block dictionary to translate.
            temp_dir: Path to a temporary directory for processing assets (e.g. images).
            escape_fn: The escape_latex callable.
            ast_to_latex_fn: Recursive call for nested block rendering.
        """
        raise NotImplementedError()
