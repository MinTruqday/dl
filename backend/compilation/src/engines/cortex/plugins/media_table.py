from typing import Any, Dict
from src.engines.cortex.plugins.base import BaseBlockTranslator
from src.engines.cortex.utils import CortexUtils

class ImageTranslator(BaseBlockTranslator):
    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        url = block.get("content", "").strip()
        args = block.get("args", {})
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
            img_latex.append(f"\\caption{{{escape_fn(caption)}}}")
        if label:
            img_latex.append(f"\\label{{{label}}}")
        img_latex.append("\\end{figure}\n\n")
        return "\n".join(img_latex)

class TableTranslator(BaseBlockTranslator):
    @classmethod
    def markdown_table_to_latex(cls, table_str: str, escape_fn: Any) -> str:
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

        escaped_headers = [escape_fn(h) for h in headers]
        latex_lines.append(" & ".join(escaped_headers) + " \\\\")
        latex_lines.append("\\midrule")

        data_rows = rows[2:] if len(rows) > 1 else rows[1:]
        for row in data_rows:
            escaped_row = [escape_fn(c) for c in row]
            while len(escaped_row) < num_cols:
                escaped_row.append("")
            escaped_row = escaped_row[:num_cols]
            latex_lines.append(" & ".join(escaped_row) + " \\\\")

        latex_lines.append("\\bottomrule")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{table}")

        return "\n".join(latex_lines)

    @classmethod
    async def translate(
        cls,
        block: Dict[str, Any],
        temp_dir: str,
        escape_fn: Any,
        ast_to_latex_fn: Any,
    ) -> str:
        content = block.get("content", "")
        return cls.markdown_table_to_latex(content, escape_fn) + "\n\n"
