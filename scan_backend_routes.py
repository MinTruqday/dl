import os
import glob
import re

backend_routes = []

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('_router.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                
                # find prefix
                prefix_match = re.search(r'prefix="([^"]+)"', content)
                prefix = prefix_match.group(1) if prefix_match else ""
                
                # find endpoints
                endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\("([^"]+)"', content)
                for method, path in endpoints:
                    full_path = prefix + path
                    if full_path.endswith('/'):
                        full_path = full_path[:-1]
                    # Print the service name, prefix and full_path
                    service = filepath.split('/')[1]
                    backend_routes.append(f"{service} | {method.upper()} | {full_path}")

for r in sorted(backend_routes):
    print(r)
