import os
import re

routes = []
backend_dir = "backend"
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py") and "/api" in root:
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # find prefix
                prefix = ""
                prefix_match = re.search(r'APIRouter\(.*?prefix=["\'](.*?)["\']', content)
                if prefix_match:
                    prefix = prefix_match.group(1)
                
                # find endpoints
                endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\(["\'](.*?)["\']', content)
                for method, route in endpoints:
                    full_route = f"{method.upper()} {prefix}{route}".replace("//", "/")
                    routes.append(full_route)

routes = list(set(routes))
routes.sort()
for r in routes:
    print(r)
