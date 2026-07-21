import re
from typing import Any, Dict, List

class CortexParser:
    @staticmethod
    def parse_args(args_str: str) -> Dict[str, Any]:
        args = {}
        if not args_str:
            return args
        parts = args_str.split(",")
        for part in parts:
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                args[k.strip()] = v.strip()
            else:
                args[part] = True
        return args

    @staticmethod
    def find_matching_boundary(lines: List[str], start_idx: int) -> int:
        depth = 1
        idx = start_idx + 2
        n = len(lines)

        while idx < n:
            line = lines[idx].strip()

            if line == "::":
                prev_idx = idx - 1
                while prev_idx > start_idx and not lines[prev_idx].strip():
                    prev_idx -= 1
                
                prev_line = lines[prev_idx].strip()
                is_prev_boundary_start = False
                if prev_line.startswith("/") and ":" in prev_line:
                    content_after_colon = prev_line.split(":", 1)[1].strip()
                    if content_after_colon == "":
                        is_prev_boundary_start = True

                if is_prev_boundary_start:
                    depth += 1
                else:
                    depth -= 1
                    if depth == 0:
                        return idx

            idx += 1
        return -1

    @classmethod
    def parse_list_items(cls, content: str) -> List[str]:
        lines = content.split("\n")
        items = []
        current_item = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* ") or re.match(r"^\d+\.\s+", stripped):
                if current_item:
                    items.append("\n".join(current_item))
                # Strip list marker
                marker_match = re.match(r"^(?:-\s+|\*\s+|\d+\.\s+)(.*)$", stripped)
                if marker_match:
                    current_item = [marker_match.group(1).strip()]
                else:
                    current_item = [stripped]
            else:
                if stripped:
                    current_item.append(stripped)
        if current_item:
            items.append("\n".join(current_item))
        return items

    @classmethod
    def parse_to_ast(cls, content: str) -> List[Dict[str, Any]]:
        lines = content.split("\n")
        blocks = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            match = re.match(r"^/([a-zA-Z0-9_-]+)(?:\[(.*?)\])?:(.*)$", stripped)
            if match:
                keyword = match.group(1)
                args_str = match.group(2) or ""
                first_line_content = match.group(3)

                args = cls.parse_args(args_str)

                is_boundary = False
                if i + 1 < n and lines[i + 1].strip() == "::" and first_line_content.strip() == "":
                    is_boundary = True

                if is_boundary:
                    closing_idx = cls.find_matching_boundary(lines, i)
                    if closing_idx != -1:
                        inner_lines = lines[i + 2 : closing_idx]
                        inner_content = "\n".join(inner_lines)
                        i = closing_idx + 1
                    else:
                        inner_lines = lines[i + 2 :]
                        inner_content = "\n".join(inner_lines)
                        i = n

                    if keyword in ["note", "warn", "info"]:
                        children = cls.parse_to_ast(inner_content)
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "children": children,
                                "raw_content": inner_content,
                            }
                        )
                    elif keyword in ["list", "enum"]:
                        items = cls.parse_list_items(inner_content)
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "items": items,
                                "raw_content": inner_content,
                            }
                        )
                    else:
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "content": inner_content.strip(),
                                "raw_content": inner_content,
                            }
                        )
                else:
                    content_parts = []
                    is_single_line = False
                    if first_line_content.strip():
                        content_parts.append(first_line_content.strip())
                        is_single_line = True

                    i += 1
                    if not is_single_line:
                        while i < n:
                            next_line = lines[i]
                            if not next_line.strip():
                                i += 1
                                break
                            if next_line.strip().startswith("/") and ":" in next_line:
                                break
                            content_parts.append(next_line)
                            i += 1

                    simple_content = "\n".join(content_parts)

                    if keyword in ["note", "warn", "info"]:
                        children = cls.parse_to_ast(simple_content)
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "children": children,
                                "raw_content": simple_content,
                            }
                        )
                    elif keyword in ["list", "enum"]:
                        items = cls.parse_list_items(simple_content)
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "items": items,
                                "raw_content": simple_content,
                            }
                        )
                    else:
                        blocks.append(
                            {
                                "type": keyword,
                                "args": args,
                                "content": simple_content.strip(),
                                "raw_content": simple_content,
                            }
                        )
            else:
                para_parts = [line]
                i += 1
                while i < n:
                    next_line = lines[i]
                    if not next_line.strip():
                        i += 1
                        break
                    if next_line.strip().startswith("/") and ":" in next_line:
                        break
                    para_parts.append(next_line)
                    i += 1

                para_content = "\n".join(para_parts)
                blocks.append(
                    {"type": "paragraph", "content": para_content, "args": {}}
                )
        return blocks
