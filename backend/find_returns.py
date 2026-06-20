import os
import ast
import re

findings = []

class ReturnStringFinder(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath

    def visit_Return(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            s = node.value.value
            if re.search(r'[a-zA-Z]', s) and not re.search(r'[\u0080-\uFFFF]', s):
                findings.append(f"{self.filepath}:{node.lineno} -> {s}")
        self.generic_visit(node)

for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    tree = ast.parse(file.read())
                finder = ReturnStringFinder(path)
                finder.visit(tree)
            except Exception as e:
                pass

with open('missed_returns.txt', 'w', encoding='utf-8') as out:
    for item in findings:
        out.write(item + "\n")
print(f"Found {len(findings)} returned english strings.")
