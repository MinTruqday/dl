import os
import re

print("--- ROUTER PREFIXES ---")
for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            prefixes = re.findall(r'prefix=["\']([^"\']+)["\']', content)
            for p in prefixes:
                print(f"{path}: prefix={p}")

print("\n--- ROUTER PATHS ---")
for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py") and "router" in root:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for line in lines:
                match = re.search(
                    r'@router\.(get|post|put|patch|delete|websocket)\(["\']([^"\']*)["\']',
                    line,
                )
                if match:
                    print(f"{path}: {match.group(1).upper()} {match.group(2)}")

print("\n--- INTERNAL API CALLS ---")
for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if "_URL" in line and ("/" in line or 'f"' in line or "f'" in line):
                    match = re.search(r'f["\'].*_URL\}/([^"\']+)["\']', line)
                    if match:
                        print(f"{path}: /{match.group(1)}")
