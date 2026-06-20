import os
import re

for root, _, files in os.walk('agentic_ai'):
    if 'venv' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                if re.search(r'["\'].*[\u0080-\uFFFF]+.*["\']', line):
                    strings = re.findall(r'["\']([^"\']*)["\']', line)
                    for s in strings:
                        if re.search(r'[\u0080-\uFFFF]', s):
                            print(f"{path}:{i+1} -> {s}")
