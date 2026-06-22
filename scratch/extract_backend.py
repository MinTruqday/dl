import ast
import os
import re

backend_routes = []
backend_dir = "backend"

for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py") and "/api" in root:
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
                
            prefix = ""
            for node in ast.walk(tree):
                # find prefix = APIRouter(prefix="/foo")
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    if isinstance(node.targets[0], ast.Name) and node.targets[0].id == "router":
                        if isinstance(node.value, ast.Call):
                            for kw in node.value.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                    prefix = kw.value.value
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "router":
                                method = decorator.func.attr.upper()
                                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                                    route = decorator.args[0].value
                                    full_route = f"{method} {prefix}{route}".replace("//", "/")
                                    backend_routes.append(full_route)

# Now frontend
frontend_routes = []
frontend_dir = "frontend/features"
for root, dirs, files in os.walk(frontend_dir):
    if "services" in root:
        for file in files:
            if file.endswith((".ts", ".tsx")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'fetch\(\s*[`\'"]\$\{API_URL\}(.*?)[`\'"\?#]', content)
                    for route in matches:
                        route = route.split('?')[0]
                        frontend_routes.append((path, route))

# Normalize backend
backend_prefixes = []
for br in backend_routes:
    method, path = br.split(" ", 1)
    prefix = path.split("{")[0]
    if prefix.endswith("/"): prefix = prefix[:-1]
    if prefix:
        backend_prefixes.append(prefix)

missing_count = 0
for path, route in frontend_routes:
    route_prefix = route.split("${")[0]
    if route_prefix.endswith("/"): route_prefix = route_prefix[:-1]
    
    found = False
    for br_prefix in backend_prefixes:
        if br_prefix == route_prefix or route_prefix.startswith(br_prefix) or (br_prefix and br_prefix.startswith(route_prefix)):
            found = True
            break
            
    if not found:
        print(f"MISSING: {route} IN {path}")
        missing_count += 1
        
if missing_count == 0:
    print("All match!")
