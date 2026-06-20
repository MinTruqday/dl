import os
import ast

imports = set()

for root, _, files in os.walk('backend'):
    if 'venv' in root or 'node_modules' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                try:
                    tree = ast.parse(file.read(), filename=path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.add(node.module.split('.')[0])
                except SyntaxError:
                    pass

for imp in sorted(imports):
    print(imp)
