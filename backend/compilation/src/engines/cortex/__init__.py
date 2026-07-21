import tempfile
from typing import Any, Dict, List
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.engines.latex import LatexEngine
from src.engines.cortex.parser import CortexParser
from src.engines.cortex.translator import CortexTranslator
from src.engines.cortex.formatter import CortexFormatter
from src.engines.cortex.utils import CortexUtils

class CortexEngine:
    @staticmethod
    def parse_args(args_str: str) -> Dict[str, Any]:
        return CortexParser.parse_args(args_str)

    @staticmethod
    def find_matching_boundary(lines: List[str], start_idx: int) -> int:
        return CortexParser.find_matching_boundary(lines, start_idx)

    @classmethod
    def parse_to_ast(cls, content: str) -> List[Dict[str, Any]]:
        return CortexParser.parse_to_ast(content)

    @classmethod
    def escape_latex(cls, text: str) -> str:
        return CortexTranslator.escape_latex(text)

    @classmethod
    def markdown_table_to_latex(cls, table_str: str) -> str:
        return CortexTranslator.markdown_table_to_latex(table_str)

    @classmethod
    async def ast_to_latex(cls, blocks: List[Dict[str, Any]], temp_dir: str) -> str:
        return await CortexTranslator.ast_to_latex(blocks, temp_dir)

    @classmethod
    async def compile_to_pdf(cls, content: str) -> bytes:
        logger.info("Starting Cortex compilation to PDF")
        temp_dir = tempfile.gettempdir()
        blocks = cls.parse_to_ast(content)

        # Extract metadata blocks if present
        title_block = next((b for b in blocks if b["type"] == "title"), None)
        author_block = next((b for b in blocks if b["type"] == "author"), None)
        date_block = next((b for b in blocks if b["type"] == "date"), None)
        copyright_block = next((b for b in blocks if b["type"] == "copyright"), None)

        meta_preamble = []
        if title_block:
            t_text = cls.escape_latex(title_block.get("content", ""))
            if copyright_block:
                c_text = cls.escape_latex(copyright_block.get("content", ""))
                meta_preamble.append(f"\\title{{{t_text}\\thanks{{{c_text}}}}}")
            else:
                meta_preamble.append(f"\\title{{{t_text}}}")
        if author_block:
            a_text = cls.escape_latex(author_block.get("content", ""))
            meta_preamble.append(f"\\author{{{a_text}}}")
        if date_block:
            d_text = date_block.get("content", "").strip()
            if d_text:
                meta_preamble.append(f"\\date{{{cls.escape_latex(d_text)}}}")
            else:
                meta_preamble.append("\\date{\\today}")

        meta_preamble_str = "\n".join(meta_preamble) + "\n\n" if meta_preamble else ""

        body_latex = await cls.ast_to_latex(blocks, temp_dir)
        if title_block:
            body_latex = "\\maketitle\n\n" + body_latex

        preamble = (
            "\\documentclass{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[T5]{fontenc}\n"
            "\\usepackage{amsmath,amssymb}\n"
            "\\usepackage{graphicx}\n"
            "\\usepackage{booktabs}\n"
            "\\usepackage{listings}\n"
            "\\usepackage{xcolor}\n"
            "\\usepackage{geometry}\n"
            "\\geometry{a4paper, margin=1in}\n"
            "\\usepackage{hyperref}\n"
            "\\usepackage{tcolorbox}\n"
            "\\tcbuselibrary{skins,breakable}\n\n"
            "\\definecolor{noteback}{HTML}{F5F5F7}\n"
            "\\definecolor{noteframe}{HTML}{0071E3}\n"
            "\\definecolor{warnback}{HTML}{FFF5F5}\n"
            "\\definecolor{warnframe}{HTML}{FF3B30}\n"
            "\\definecolor{infoback}{HTML}{F4FBF7}\n"
            "\\definecolor{infoframe}{HTML}{34C759}\n\n"
            "\\newtcolorbox{cortexnote}{\n"
            "  colback=noteback,\n"
            "  colframe=noteframe,\n"
            "  fonttitle=\\bfseries,\n"
            "  title={Ghi chú},\n"
            "  arc=3mm,\n"
            "  breakable\n"
            "}\n\n"
            "\\newtcolorbox{cortexwarn}{\n"
            "  colback=warnback,\n"
            "  colframe=warnframe,\n"
            "  fonttitle=\\bfseries,\n"
            "  title={Cảnh báo},\n"
            "  arc=3mm,\n"
            "  breakable\n"
            "}\n\n"
            "\\newtcolorbox{cortexinfo}{\n"
            "  colback=infoback,\n"
            "  colframe=infoframe,\n"
            "  fonttitle=\\bfseries,\n"
            "  title={Thông tin},\n"
            "  arc=3mm,\n"
            "  breakable\n"
            "}\n\n"
            "\\lstset{\n"
            "  basicstyle=\\ttfamily\\small,\n"
            "  commentstyle=\\color{gray},\n"
            "  keywordstyle=\\color{blue},\n"
            "  stringstyle=\\color{red},\n"
            "  breaklines=true,\n"
            "  frame=single,\n"
            "  showstringspaces=false,\n"
            "  backgroundcolor=\\color{noteback}\n"
            "}\n\n"
        )

        full_latex = preamble + meta_preamble_str + "\\begin{document}\n" + body_latex + "\\end{document}\n"
        logger.info("Cortex document translated to LaTeX successfully")

        return await LatexEngine.compile_to_pdf(full_latex)

    @classmethod
    def compile_to_doclibx(cls, content: str) -> bytes:
        blocks = cls.parse_to_ast(content)
        return CortexUtils.compile_to_doclibx(content, blocks, settings.VERSION)

    @classmethod
    def format_markdown_table(cls, table_str: str) -> str:
        return CortexFormatter.format_markdown_table(table_str)

    @classmethod
    def format_cortex(cls, content: str) -> str:
        blocks = cls.parse_to_ast(content)
        return CortexFormatter.format_cortex(blocks)
