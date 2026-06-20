import ast
import os

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or "core" in root or "venv" in root:
        continue
    for f in files:
        if f.endswith(".py") and f != "__init__.py":
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                tree = ast.parse(content)
                classes = [
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                ]
                if classes:
                    print(f"{path}: {classes}")
                else:
                    # If no classes, it might be just functions or router
                    # print(f"{path}: NO CLASSES")
                    pass
            except Exception as e:
                print(f"Error reading {path}: {e}")
