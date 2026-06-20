import os
import re

services = ['agentic_ai', 'authentication', 'collector', 'content', 'editor', 'finance', 'management', 'messaging', 'notification', 'realtime']

cross_imports = []

for root, _, files in os.walk('backend'):
    if 'venv' in root or 'node_modules' in root or '__pycache__' in root:
        continue
    # Determine current service context
    current_service = None
    for svc in services:
        if f'backend/{svc}' in root or root == f'backend/{svc}':
            current_service = svc
            break
            
    if not current_service:
        continue
        
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Look for imports from other services
                for svc in services:
                    if svc != current_service:
                        # Matches 'import service' or 'from service'
                        pattern = rf'^(?:from|import)\s+{svc}\b'
                        if re.search(pattern, line):
                            cross_imports.append((path, line_num, line.strip()))

if cross_imports:
    print("Found cross-service imports (Monolith leaking):")
    for path, line_num, line in cross_imports:
        print(f"{path}:{line_num}: {line}")
else:
    print("No cross-service imports found!")
