import os
import re

service_prefixes = {}

for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root or '.git' in root or 'core' in root:
        continue
    for f in files:
        if f.endswith('.py') and 'router' in root:
            # Determine service name from the path (e.g. backend/content/src/... -> content)
            # root looks like ./content/src/router
            parts = root.split(os.sep)
            if len(parts) >= 2:
                service = parts[1]
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                prefixes = re.findall(r'prefix=["\']([^"\']+)["\']', content)
                for p in prefixes:
                    if service not in service_prefixes:
                        service_prefixes[service] = set()
                    service_prefixes[service].add(p)

for service, prefixes in service_prefixes.items():
    print(f"Service: {service}")
    for p in sorted(prefixes):
        print(f"  {p}")
