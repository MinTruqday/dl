import os
import re
from typing import Any, Dict, List
from src.engines.cortex.utils import CortexUtils

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
        lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
        if not lines:
            return ""

        rows = []
        for line in lines:
            if "|" in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) > 1 and cells[0] == "":
                    cells = cells[1:]
                if len(cells) > 0 and cells[-1] == "":
                    cells = cells[:-1]
                rows.append(cells)

        if not rows:
            return ""

        headers = rows[0]
        num_cols = len(headers)

        alignments = []
        if len(rows) > 1:
            sep_row = rows[1]
            for col_idx in range(num_cols):
                cell = sep_row[col_idx] if col_idx < len(sep_row) else ""
                if cell.startswith(":") and cell.endswith(":"):
                    alignments.append("c")
                elif cell.endswith(":"):
                    alignments.append("r")
                else:
                    alignments.append("l")
        else:
            alignments = ["l"] * num_cols

        align_str = "".join(alignments)
        latex_lines = [
            "\\begin{table}[h]",
            "\\centering",
            f"\\begin{{tabular}}{{{align_str}}}",
            "\\toprule",
        ]

        escaped_headers = [cls.escape_latex(h) for h in headers]
        latex_lines.append(" & ".join(escaped_headers) + " \\\\")
        latex_lines.append("\\midrule")

        data_rows = rows[2:] if len(rows) > 1 else rows[1:]
        for row in data_rows:
            escaped_row = [cls.escape_latex(c) for c in row]
            while len(escaped_row) < num_cols:
                escaped_row.append("")
            escaped_row = escaped_row[:num_cols]
            latex_lines.append(" & ".join(escaped_row) + " \\\\")

        latex_lines.append("\\bottomrule")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{table}")

        return "\n".join(latex_lines)

    @classmethod
    async def ast_to_latex(cls, blocks: List[Dict[str, Any]], temp_dir: str) -> str:
        latex_blocks = []
        for block in blocks:
            b_type = block.get("type")
            args = block.get("args", {})

            if b_type in ["title", "author", "date", "copyright"]:
                continue

            elif b_type == "paragraph":
                content = block.get("content", "")
                latex_blocks.append(cls.escape_latex(content) + "\n\n")

            elif b_type in ["h1", "h2", "h3"]:
                content = block.get("content", "")
                escaped = cls.escape_latex(content)
                if b_type == "h1":
                    latex_blocks.append(f"\\section{{{escaped}}}\n\n")
                elif b_type == "h2":
                    latex_blocks.append(f"\\subsection{{{escaped}}}\n\n")
                elif b_type == "h3":
                    latex_blocks.append(f"\\subsubsection{{{escaped}}}\n\n")

            elif b_type in ["note", "warn", "info"]:
                children_latex = await cls.ast_to_latex(block.get("children", []), temp_dir)
                latex_blocks.append(
                    f"\\begin{{cortex{b_type}}}\n{children_latex.strip()}\n\\end{{cortex{b_type}}}\n\n"
                )

            elif b_type == "math":
                content = block.get("content", "")
                if "inline" in args:
                    latex_blocks.append(f"${content.strip()}$")
                elif "label" in args:
                    label = args.get("label")
                    latex_blocks.append(
                        f"\\begin{{equation}}\\label{{{label}}}\n{content.strip()}\n\\end{{equation}}\n\n"
                    )
                else:
                    latex_blocks.append(f"\\[\n{content.strip()}\n\\]\n\n")

            elif b_type == "code":
                content = block.get("content", "")
                lang = args.get("lang")
                if not lang:
                    for k, v in args.items():
                        if v is True:
                            lang = k
                            break
                if lang:
                    latex_blocks.append(
                        f"\\begin{{lstlisting}}[language={lang}]\n{content}\n\\end{{lstlisting}}\n\n"
                    )
                else:
                    latex_blocks.append(
                        f"\\begin{{lstlisting}}\n{content}\n\\end{{lstlisting}}\n\n"
                    )

            elif b_type == "img":
                url = block.get("content", "").strip()
                local_file = await CortexUtils.download_image(url, temp_dir)
                width = args.get("width", "0.8\\textwidth")
                if "px" in width:
                    try:
                        px_val = int(width.replace("px", "").strip())
                        width = f"{min(1.0, px_val / 800.0):.2f}\\textwidth"
                    except ValueError:
                        width = "0.8\\textwidth"

                caption = args.get("caption")
                label = args.get("label")

                img_latex = [
                    "\\begin{figure}[h]",
                    "\\centering",
                    f"\\includegraphics[width={width}]{{{local_file}}}",
                ]
                if caption:
                    img_latex.append(f"\\caption{{{cls.escape_latex(caption)}}}")
                if label:
                    img_latex.append(f"\\label{{{label}}}")
                img_latex.append("\\end{figure}\n\n")
                latex_blocks.append("\n".join(img_latex))

            elif b_type == "tbl":
                content = block.get("content", "")
                latex_blocks.append(cls.markdown_table_to_latex(content) + "\n\n")

            elif b_type in ["list", "enum"]:
                latex_env = "itemize" if b_type == "list" else "enumerate"
                items_latex = []
                for item in block.get("items", []):
                    items_latex.append(f"  \\item {cls.escape_latex(item)}")
                items_str = "\n".join(items_latex)
                latex_blocks.append(f"\\begin{{{latex_env}}}\n{items_str}\n\\end{{{latex_env}}}\n\n")

            elif b_type == "cite":
                content = block.get("content", "").strip()
                if not content:
                    for k, v in args.items():
                        if v is True:
                            content = k
                            break
                latex_blocks.append(f"\\cite{{{content}}}")

            elif b_type == "ref":
                content = block.get("content", "").strip()
                if not content:
                    for k, v in args.items():
                        if v is True:
                            content = k
                            break
                latex_blocks.append(f"\\ref{{{content}}}")

            elif b_type == "bibliography":
                content = block.get("content", "").strip()
                style = args.get("style", "plain")
                latex_blocks.append(f"\\bibliographystyle{{{style}}}\n\\bibliography{{{content}}}\n\n")

            elif b_type in ["raw", "latex"]:
                content = block.get("content", "")
                latex_blocks.append(content + "\n\n")

        return "".join(latex_blocks)
