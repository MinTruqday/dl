import ast
import os
import sys


def check_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except Exception as e:
            print(f"Syntax error in {filepath}: {e}")
            return False

    all_ok = True
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("src."):
                parts = node.module.split(".")
                # It should map to a directory or a file in the same service
                # Example: src.router.user -> file: src/router/user.py
                service_dir = os.path.dirname(os.path.dirname(filepath))
                if os.path.basename(service_dir) == "src":
                    service_dir = os.path.dirname(service_dir)

                path_dir = os.path.join(service_dir, *parts)
                path_file = path_dir + ".py"

                if not os.path.exists(path_dir) and not os.path.exists(path_file):
                    print(
                        f"[ERROR] Broken import in {filepath}: '{node.module}' -> Expected {path_dir} or {path_file}"
                    )
                    all_ok = False
    return all_ok


all_passed = True
for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            if not check_file(os.path.join(root, f)):
                all_passed = False

if all_passed:
    print("All internal src.* imports are structurally valid!")
else:
    sys.exit(1)
