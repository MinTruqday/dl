from typing import Any, Dict, List
from loguru import logger

class CortexFormatter:
    @classmethod
    def format_markdown_table(cls, table_str: str) -> str:
        lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
        if not lines:
            return table_str

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
            return table_str

        num_cols = max(len(row) for row in rows)
        widths = [0] * num_cols
        for row in rows:
            for i in range(min(len(row), num_cols)):
                widths[i] = max(widths[i], len(row[i]))

        formatted_lines = []
        for r_idx, row in enumerate(rows):
            if r_idx == 1:
                sep_cells = []
                for col_idx in range(num_cols):
                    cell = row[col_idx] if col_idx < len(row) else "---"
                    align = "left"
                    if cell.startswith(":") and cell.endswith(":"):
                        align = "center"
                    elif cell.endswith(":"):
                        align = "right"

                    if align == "center":
                        sep_cells.append(":" + "-" * (widths[col_idx] - 2) + ":")
                    elif align == "right":
                        sep_cells.append("-" * (widths[col_idx] - 1) + ":")
                    else:
                        sep_cells.append(":" + "-" * (widths[col_idx] - 1))
                formatted_lines.append("| " + " | ".join(sep_cells) + " |")
            else:
                padded_cells = []
                for col_idx in range(num_cols):
                    cell = row[col_idx] if col_idx < len(row) else ""
                    padded_cells.append(cell.ljust(widths[col_idx]))
                formatted_lines.append("| " + " | ".join(padded_cells) + " |")

        return "\n".join(formatted_lines)

    @classmethod
    def format_cortex(cls, blocks: List[Dict[str, Any]]) -> str:
        logger.info("Formatting Cortex blocks")
        formatted_parts = []

        for block in blocks:
            b_type = block.get("type")
            args = block.get("args", {})

            args_str = ""
            if args:
                args_list = []
                for k, v in args.items():
                    if v is True:
                        args_list.append(k)
                    else:
                        args_list.append(f"{k}={v}")
                args_str = f"[{','.join(args_list)}]"

            if b_type == "paragraph":
                formatted_parts.append(block.get("content", "").strip())

            elif b_type in ["h1", "h2", "h3"]:
                formatted_parts.append(f"/{b_type}: {block.get('content', '').strip()}")

            elif b_type in ["note", "warn", "info"]:
                children_formatted = cls.format_cortex(block.get("children", []))
                formatted_parts.append(
                    f"/{b_type}{args_str}:\n::\n{children_formatted.strip()}\n::"
                )

            elif b_type == "math":
                formatted_parts.append(
                    f"/math{args_str}: {block.get('content', '').strip()}"
                )

            elif b_type == "code":
                formatted_parts.append(
                    f"/code{args_str}:\n::\n{block.get('content', '')}\n::"
                )

            elif b_type == "img":
                formatted_parts.append(
                    f"/img{args_str}: {block.get('content', '').strip()}"
                )

            elif b_type == "tbl":
                formatted_table = cls.format_markdown_table(block.get("content", ""))
                formatted_parts.append(f"/tbl:\n{formatted_table}")

            elif b_type in ["list", "enum"]:
                items_str = "\n".join([f"- {item}" for item in block.get("items", [])])
                formatted_parts.append(f"/{b_type}{args_str}:\n::\n{items_str}\n::")

            elif b_type in ["cite", "ref", "title", "author", "date", "copyright"]:
                content = block.get("content", "").strip()
                formatted_parts.append(f"/{b_type}: {content}")

            elif b_type == "bibliography":
                content = block.get("content", "").strip()
                formatted_parts.append(f"/bibliography{args_str}: {content}")

            elif b_type in ["raw", "latex"]:
                formatted_parts.append(f"/{b_type}:\n::\n{block.get('content', '')}\n::")

        return "\n\n".join(formatted_parts)
