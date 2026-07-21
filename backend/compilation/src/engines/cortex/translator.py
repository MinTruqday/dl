import re
from typing import Any, Dict, List
from loguru import logger
from src.engines.cortex.plugins.registry import TRANSLATOR_REGISTRY

class CortexTranslator:
    @classmethod
    def escape_latex(cls, text: str) -> str:
        parts = text.split("$")
        for i in range(len(parts)):
            if i % 2 == 0:
                t = parts[i]

                # 1. Protect inline \cite and \ref commands (use no-underscore placeholders)
                cite_placeholders = []
                cites = re.findall(r"\\cite\{([a-zA-Z0-9_:-]+)\}", t)
                for idx, c in enumerate(cites):
                    placeholder = f"CITEPH{idx}"
                    t = t.replace(f"\\cite{{{c}}}", placeholder)
                    cite_placeholders.append((placeholder, f"\\cite{{{c}}}"))

                ref_placeholders = []
                refs = re.findall(r"\\ref\{([a-zA-Z0-9_:-]+)\}", t)
                for idx, r in enumerate(refs):
                    placeholder = f"REFPH{idx}"
                    t = t.replace(f"\\ref{{{r}}}", placeholder)
                    ref_placeholders.append((placeholder, f"\\ref{{{r}}}"))

                # 2. Process underline syntax _text_ -> CORTEXUL[text]
                t = re.sub(r"_(.*?)_", r"CORTEXUL[\1]", t)

                # 3. Escape standard LaTeX special characters
                t = t.replace("\\", "\\textbackslash{}")
                t = t.replace("&", "\\&")
                t = t.replace("%", "\\%")
                t = t.replace("#", "\\#")
                t = t.replace("_", "\\_")
                t = t.replace("{", "\\{")
                t = t.replace("}", "\\}")
                t = t.replace("~", "\\textasciitilde{}")
                t = t.replace("^", "\\textasciicircum{}")

                # 4. Convert markdown bold and italic
                t = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", t)
                t = re.sub(r"\*(.*?)\*", r"\\textit{\1}", t)

                # 5. Restore underline CORTEXUL[text] -> \underline{text}
                t = re.sub(r"CORTEXUL\[(.*?)\]", r"\\underline{\1}", t)

                # 6. Restore protected \cite and \ref commands
                for placeholder, orig in cite_placeholders:
                    t = t.replace(placeholder, orig)
                for placeholder, orig in ref_placeholders:
                    t = t.replace(placeholder, orig)

                parts[i] = t
        return "$".join(parts)

    @classmethod
    def markdown_table_to_latex(cls, table_str: str) -> str:
        from src.engines.cortex.plugins.media_table import TableTranslator
        return TableTranslator.markdown_table_to_latex(table_str, cls.escape_latex)

    @classmethod
    async def ast_to_latex(cls, blocks: List[Dict[str, Any]], temp_dir: str) -> str:
        latex_blocks = []
        for block in blocks:
            b_type = block.get("type")
            
            # Skip metadata blocks which are rendered in the preamble/title section
            if b_type in ["title", "author", "date", "copyright"]:
                continue

            translator = TRANSLATOR_REGISTRY.get(b_type)
            if translator:
                translated_str = await translator.translate(
                    block=block,
                    temp_dir=temp_dir,
                    escape_fn=cls.escape_latex,
                    ast_to_latex_fn=cls.ast_to_latex,
                )
                latex_blocks.append(translated_str)
            else:
                logger.warning("No translator plugin registered for block type: {}", b_type)

        return "".join(latex_blocks)
