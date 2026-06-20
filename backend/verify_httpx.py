import os
import re

print("--- INTERNAL API CALLS ---")
for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root or '.git' in root or 'core' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for i, line in enumerate(lines):
                if '_URL' in line and ('/' in line or 'f"' in line or "f'" in line):
                    match = re.search(r'f["\'].*_URL\}/([^"\']+)["\']', line)
                    if match:
                        print(f"{path}: /{match.group(1)}")
