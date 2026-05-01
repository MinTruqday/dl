import ast
import re
import os

def standardize_latex():
    filepath = 'utils/latex.py'
    if not os.path.exists(filepath): return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    # Extract existing lists
    raw_packages = []
    raw_commands = []
    raw_environments = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == 'LATEX_PACKAGES': raw_packages = ast.literal_eval(node.value)
                    elif target.id == 'LATEX_COMMANDS': raw_commands = ast.literal_eval(node.value)
                    elif target.id == 'LATEX_ENVIRONMENTS': raw_environments = ast.literal_eval(node.value)

    def clean_detail(detail, label):
        # Professional Vietnamese, Action + Object
        detail = re.sub(r'\(.*?\)', '', detail)
        detail = detail.replace('Package/Environment', '').replace('Gói', '').strip()
        detail = detail.replace('Thực hiện', '').replace('môi trường', '').replace('thuật toán', '').replace('lệnh', '').strip()
        detail = re.sub(r'\s+', ' ', detail).strip()
        
        verb = "Thực hiện"
        l_low = label.lower()
        if any(x in l_low for x in ['section', 'chapter', 'part', 'paragraph', 'begin', 'frame', 'tcolorbox', 'algorithm']):
            verb = "Tạo"
        elif any(x in l_low for x in ['cite', 'ref', 'label', 'url', 'href', 'footnote', 'gls', 'unit', 'qty', 'num']):
            verb = "Chèn"
        elif any(x in l_low for x in ['text', 'emph', 'size', 'color', 'centering', 'ragged', 'large', 'small', 'bold', 'italic', 'underline']):
            verb = "Định dạng"
        elif any(x in l_low for x in ['draw', 'plot', 'tikz', 'pgf', 'circuit']):
            verb = "Vẽ"
        elif any(x in l_low for x in ['line', 'width', 'opacity', 'rotate', 'scale', 'set', 'margin']):
            verb = "Thiết lập"

        if not detail: detail = label.strip('\\')
        detail = detail[0].upper() + detail[1:] if detail else ""
        if not any(detail.startswith(v) for v in ["Chèn", "Tạo", "Thiết lập", "Định dạng", "Căn lề", "Vẽ", "Thực hiện"]):
            detail = f"{verb} {detail.lower()}"
        return re.sub(r'\s+', ' ', detail).strip()

    def standardize_placeholders(text):
        # 1. Normalize all placeholders to English
        # Convert ${n:vietnamese} or ${n:generic} to ${n:english}
        def repl(m):
            idx = m.group(1)
            content = m.group(2).lower() if m.group(2) else ""
            
            label = "value"
            if any(x in content for x in ["text", "văn bản", "nội dung", "văn bản", "content"]): label = "text"
            elif any(x in content for x in ["title", "tiêu đề", "name", "tên"]): label = "title"
            elif any(x in content for x in ["label", "nhãn", "key", "khóa", "ref"]): label = "label"
            elif any(x in content for x in ["option", "tùy chọn", "spec"]): label = "options"
            elif any(x in content for x in ["package", "gói", "class", "lớp"]): label = "package"
            elif any(x in content for x in ["color", "màu"]): label = "color"
            elif any(x in content for x in ["width", "độ dày", "size"]): label = "width"
            elif any(x in content for x in ["angle", "góc"]): label = "angle"
            elif any(x in content for x in ["factor", "hệ số", "scale"]): label = "scale"
            
            return f"${{{idx}:{label}}}"

        # Fix broken missing $
        text = re.sub(r'(?<!\$)\{(\d+):([^}]*)\}', r'${\1:\2}', text)
        # Normalize labels
        text = re.sub(r'\$\{(\d+):([^}]*)\}', repl, text)
        # Fix $1 or ${1}
        text = re.sub(r'\$(?:(\d+)|\{(\d+)\})', lambda m: f"${{{m.group(1) or m.group(2)}:value}}", text)
        
        # 2. Fix literal "1" artifacts (like \hat{1}, \ddot{1})
        text = re.sub(r'\{1\}', r'{${1:value}}', text)
        
        return text

    def process_items(items):
        processed = []
        seen_inserts = set()
        
        # Generic collapse patterns
        collapse_patterns = [
            (r'^\\usetheme{.*', 'usetheme', '\\\\usetheme{${1:theme}}', 'Thiết lập giao diện Beamer'),
            (r'^\\usecolortheme{.*', 'usecolortheme', '\\\\usecolortheme{${1:color_theme}}', 'Thiết lập màu giao diện Beamer'),
            (r'^\\color{.*', 'color', '\\\\color{${1:color}}', 'Thiết lập màu'),
            (r'^line width.*', 'line width', 'line width=${1:width}pt', 'Thiết lập độ dày đường'),
        ]

        for item in items:
            label = item['label']
            insert = standardize_placeholders(item['insertText'])
            
            # Additional literal fixes
            if insert.endswith("{1}"): insert = insert[:-3] + "{${1:value}}"
            
            # Check collapse
            collapsed = False
            for pattern, new_label, new_insert, new_detail in collapse_patterns:
                if re.match(pattern, label) or re.match(pattern, insert):
                    if new_insert not in seen_inserts:
                        processed.append({
                            "label": new_label, "insertText": new_insert, "detail": new_detail, "type": "snippet"
                        })
                        seen_inserts.add(new_insert)
                    collapsed = True
                    break
            
            if not collapsed:
                if insert not in seen_inserts:
                    item['insertText'] = insert
                    # Standardize label to remove artifacts like $1:text
                    item['label'] = re.sub(r'\$\{?\d+:[^}]*\}?', '...', item['label'])
                    item['detail'] = clean_detail(item['detail'], label)
                    processed.append(item)
                    seen_inserts.add(insert)
        return processed

    clean_commands = process_items(raw_commands)
    clean_envs = process_items(raw_environments)
    clean_pkgs = process_items(raw_packages)

    # Sort
    def get_sort_score(item):
        label = item['label'].lower()
        if 'documentclass' in label: return 0
        if 'usepackage' in label: return 1
        if any(x in label for x in ['author', 'title', 'date', 'maketitle']): return 2
        if any(x in label for x in ['part', 'chapter', 'section', 'subsection']): return 3
        return 10

    clean_commands.sort(key=lambda x: (get_sort_score(x), x['label']))
    clean_envs.sort(key=lambda x: (get_sort_score(x), x['label']))
    clean_pkgs.sort(key=lambda x: (get_sort_score(x), x['label']))

    def gen(name, items):
        res = f"{name} = [\n"
        for item in items:
            res += "    {\n"
            for k, v in item.items():
                v_esc = v.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')
                res += f'        "{k}": "{v_esc}",\n'
            res = res.rstrip(',\n') + "\n    },\n"
        return res.rstrip(',\n') + "\n]"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("from typing import Any\nfrom core.response import APIResponse\n\n")
        f.write(gen("LATEX_PACKAGES", clean_pkgs) + "\n\n")
        f.write(gen("LATEX_COMMANDS", clean_commands) + "\n\n")
        f.write(gen("LATEX_ENVIRONMENTS", clean_envs) + "\n")

if __name__ == "__main__":
    standardize_latex()
