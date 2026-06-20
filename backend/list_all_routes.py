import os
import re

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py") and "router" in root:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            # Find all prefix definitions
            prefixes = re.findall(r'prefix=["\']([^"\']+)["\']', content)
            # Find all router paths, allowing newlines and spaces before the quote
            routes = re.findall(
                r'@router\.(?:get|post|put|patch|delete|websocket)\(\s*["\']([^"\']*)["\']',
                content,
            )

            for p in prefixes:
                print(f"{path}: prefix {p}")
            for r in routes:
                print(f"{path}: route {r}")
