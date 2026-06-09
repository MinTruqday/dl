import re
import html
from typing import Optional
from loguru import logger
from src.schemas.editorjs import EditorJSContent, EditorBlock
from src.services.latex_engine import LatexEngine


class EditorJSEngine:
    """
    Converts EditorJS block JSON to LaTeX, then compiles to PDF (or exports).
    """

    HEADING_LEVELS = {1: "section", 2: "subsection", 3: "subsubsection", 4: "paragraph", 5: "subparagraph", 6: "subparagraph"}

    @staticmethod
    def _escape(text: str) -> str:
        """Escape special LaTeX characters from plain text."""
        if not text:
            return ""
        specials = {
            "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
            "^": r"\^{}", "\\": r"\textbackslash{}",
        }
        return "".join(specials.get(c, c) for c in str(text))

    @staticmethod
    def _strip_html_tags(text: str) -> str:
        """Strip HTML tags but preserve bold/italic/code."""
        # Bold
        text = re.sub(r"<b>(.*?)</b>", r"\\textbf{\1}", text, flags=re.DOTALL)
        text = re.sub(r"<strong>(.*?)</strong>", r"\\textbf{\1}", text, flags=re.DOTALL)
        # Italic
        text = re.sub(r"<i>(.*?)</i>", r"\\textit{\1}", text, flags=re.DOTALL)
        text = re.sub(r"<em>(.*?)</em>", r"\\textit{\1}", text, flags=re.DOTALL)
        # Inline code
        text = re.sub(r"<code>(.*?)</code>", r"\\texttt{\1}", text, flags=re.DOTALL)
        # Mark (highlight)
        text = re.sub(r"<mark[^>]*>(.*?)</mark>", r"\\colorbox{yellow}{\1}", text, flags=re.DOTALL)
        # Links
        text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"\\href{\1}{\2}", text, flags=re.DOTALL)
        # Remove remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)

    @staticmethod
    def _block_to_latex(block: EditorBlock) -> str:
        btype = block.type
        data = block.data

        if btype == "header":
            level = data.get("level", 2)
            text = EditorJSEngine._strip_html_tags(data.get("text", ""))
            cmd = EditorJSEngine.HEADING_LEVELS.get(level, "section")
            return f"\\{cmd}{{{text}}}\n"

        elif btype == "paragraph":
            text = EditorJSEngine._strip_html_tags(data.get("text", ""))
            return f"{text}\n\n"

        elif btype == "list":
            style = data.get("style", "unordered")
            items = data.get("items", [])
            env = "itemize" if style == "unordered" else "enumerate"
            items_tex = "\n".join(
                f"  \\item {EditorJSEngine._strip_html_tags(item)}" for item in items
            )
            return f"\\begin{{{env}}}\n{items_tex}\n\\end{{{env}}}\n\n"

        elif btype == "checklist":
            items = data.get("items", [])
            lines = []
            for item in items:
                checked = "[x]" if item.get("checked") else "[ ]"
                text = EditorJSEngine._strip_html_tags(item.get("text", ""))
                lines.append(f"  \\item[{checked}] {text}")
            return f"\\begin{{itemize}}\n" + "\n".join(lines) + "\n\\end{itemize}\n\n"

        elif btype == "code":
            code = data.get("code", "")
            lang = data.get("language", "")
            return f"\\begin{{verbatim}}\n{code}\n\\end{{verbatim}}\n\n"

        elif btype == "quote":
            text = EditorJSEngine._strip_html_tags(data.get("text", ""))
            caption = EditorJSEngine._strip_html_tags(data.get("caption", ""))
            caption_tex = f"\n\\caption{{{caption}}}" if caption else ""
            return f"\\begin{{quote}}\n{text}{caption_tex}\n\\end{{quote}}\n\n"

        elif btype == "delimiter":
            return "\\begin{center}\\rule{0.5\\linewidth}{0.4pt}\\end{center}\n\n"

        elif btype == "warning":
            title = EditorJSEngine._strip_html_tags(data.get("title", "Lưu ý"))
            message = EditorJSEngine._strip_html_tags(data.get("message", ""))
            return f"\\textbf{{{title}:}} {message}\n\n"

        elif btype == "table":
            content = data.get("content", [])
            if not content:
                return ""
            cols = len(content[0]) if content else 1
            col_spec = "|" + "|".join(["l"] * cols) + "|"
            rows = []
            for i, row in enumerate(content):
                cells = " & ".join(EditorJSEngine._strip_html_tags(cell) for cell in row)
                rows.append(f"  {cells} \\\\")
                if i == 0:
                    rows.append("  \\hline")
            return (
                f"\\begin{{tabular}}{{{col_spec}}}\n\\hline\n"
                + "\n".join(rows)
                + "\n\\hline\n\\end{{tabular}}\n\n"
            )

        elif btype == "image":
            url = data.get("url") or data.get("file", {}).get("url", "")
            caption = EditorJSEngine._strip_html_tags(data.get("caption", ""))
            caption_tex = f"\\caption{{{caption}}}" if caption else ""
            return (
                f"\\begin{{figure}}[h]\n"
                f"  \\centering\n"
                f"  \\includegraphics[width=0.8\\linewidth]{{{url}}}\n"
                f"  {caption_tex}\n"
                f"\\end{{figure}}\n\n"
            )

        elif btype == "math":
            formula = data.get("formula", data.get("text", ""))
            return f"\\[\n{formula}\n\\]\n\n"

        # Unknown block types — skip silently
        logger.debug(f"EditorJSEngine: Skipping unknown block type '{btype}'")
        return ""

    @staticmethod
    def to_latex(
        content: EditorJSContent,
        title: Optional[str] = None,
        author: Optional[str] = None,
        font_size: int = 12,
        paper_size: str = "a4paper",
    ) -> str:
        body_parts = [EditorJSEngine._block_to_latex(b) for b in content.blocks]
        body = "".join(body_parts)

        title_tex = f"\\title{{{EditorJSEngine._escape(title)}}}\n" if title else ""
        author_tex = f"\\author{{{EditorJSEngine._escape(author)}}}\n" if author else ""
        maketitle_tex = "\\maketitle\n\n" if (title or author) else ""

        return (
            f"\\documentclass[{font_size}pt,{paper_size}]{{article}}\n"
            f"\\usepackage[utf8]{{inputenc}}\n"
            f"\\usepackage[T1]{{fontenc}}\n"
            f"\\usepackage{{geometry}}\n"
            f"\\usepackage{{hyperref}}\n"
            f"\\usepackage{{graphicx}}\n"
            f"\\usepackage{{xcolor}}\n"
            f"\\usepackage{{booktabs}}\n"
            f"\\geometry{{margin=2.5cm}}\n"
            f"{title_tex}"
            f"{author_tex}"
            f"\\begin{{document}}\n"
            f"{maketitle_tex}"
            f"{body}"
            f"\\end{{document}}\n"
        )

    @staticmethod
    async def compile_to_pdf(
        content: EditorJSContent,
        title: Optional[str] = None,
        author: Optional[str] = None,
        font_size: int = 12,
        paper_size: str = "a4paper",
    ) -> bytes:
        latex_source = EditorJSEngine.to_latex(content, title, author, font_size, paper_size)
        logger.info(f"EditorJSEngine: Compiled {len(content.blocks)} blocks to LaTeX ({len(latex_source)} chars)")
        return await LatexEngine.compile_to_pdf(latex_source)

    @staticmethod
    async def export_to_format(
        content: EditorJSContent,
        target_format: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
    ) -> bytes:
        latex_source = EditorJSEngine.to_latex(content, title, author)
        return await LatexEngine.export_to_format(latex_source, target_format)
