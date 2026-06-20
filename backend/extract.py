import ast
import json
import os

target_dirs = ['.']
extracted = set()

class StringExtractor(ast.NodeVisitor):
    def visit_Call(self, node):
        # Check keyword arguments
        for kw in node.keywords:
            if kw.arg == 'detail':
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    extracted.add(kw.value.value)
                elif isinstance(kw.value, ast.JoinedStr):
                    # For f-strings, let's extract the raw pattern if possible, but user warned about "{document_id}" mapping.
                    # We might need to handle f-strings properly. Let's reconstruct the f-string template.
                    pass

        # Check Exception calls and loggers
        if isinstance(node.func, ast.Name):
            if node.func.id in ['Exception', 'ValueError', 'RuntimeError', 'TypeError', 'KeyError', 'HTTPException', 'PermissionError']:
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    extracted.add(node.args[0].value)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'logger':
                if node.func.attr in ['info', 'error', 'warning', 'debug', 'critical']:
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        extracted.add(node.args[0].value)

        self.generic_visit(node)

def reconstruct_fstring(joined_str):
    parts = []
    for value in joined_str.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            # Just extract the variable name if it's a simple name
            if isinstance(value.value, ast.Name):
                parts.append(f"{{{value.value.id}}}")
            else:
                parts.append("{...}")
    return "".join(parts)

class FStringExtractor(ast.NodeVisitor):
    def visit_Call(self, node):
        for kw in node.keywords:
            if kw.arg == 'detail':
                if isinstance(kw.value, ast.JoinedStr):
                    s = reconstruct_fstring(kw.value)
                    if s: extracted.add(s)

        if isinstance(node.func, ast.Name) and node.func.id in ['Exception', 'ValueError', 'RuntimeError', 'TypeError', 'KeyError', 'HTTPException', 'PermissionError']:
            if node.args and isinstance(node.args[0], ast.JoinedStr):
                s = reconstruct_fstring(node.args[0])
                if s: extracted.add(s)

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'logger':
            if node.func.attr in ['info', 'error', 'warning', 'debug', 'critical']:
                if node.args and isinstance(node.args[0], ast.JoinedStr):
                    s = reconstruct_fstring(node.args[0])
                    if s: extracted.add(s)
        self.generic_visit(node)

for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') and 'venv' not in root and 'node_modules' not in root:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                tree = ast.parse(content)
                extractor = StringExtractor()
                extractor.visit(tree)
                f_extractor = FStringExtractor()
                f_extractor.visit(tree)
            except Exception as e:
                print(f"Error parsing {path}: {e}")

# Filter out very short strings or obvious non-sentences, and things that look like code
filtered = []
for s in extracted:
    s = s.strip()
    if len(s) > 10 and " " in s: # Must have spaces to be a sentence
        filtered.append(s)

with open('extracted_strings.json', 'w', encoding='utf-8') as f:
    json.dump(filtered, f, ensure_ascii=False, indent=4)

print(f"Extracted {len(filtered)} strings.")
