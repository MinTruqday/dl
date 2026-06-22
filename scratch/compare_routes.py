import os
import re

backend_routes = []
with open("scratch/extract_routes.py", "r") as f:
    pass
    
# Extract backend routes
backend_dir = "backend"
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py") and "/api" in root:
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                prefix = ""
                prefix_match = re.search(r'APIRouter\(.*?prefix=["\'](.*?)["\']', content)
                if prefix_match:
                    prefix = prefix_match.group(1)
                
                endpoints = re.findall(r'@router\.(get|post|put|delete|patch)\(["\'](.*?)["\']', content)
                for method, route in endpoints:
                    full_route = f"{method.upper()} {prefix}{route}".replace("//", "/")
                    backend_routes.append(full_route)

# Now scan frontend
frontend_routes = []
frontend_dir = "frontend/features"
for root, dirs, files in os.walk(frontend_dir):
    if "services" in root:
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'fetch\(\s*[`\'"]\$\{API_URL\}(.*?)[`\'"\?#]', content)
                    for route in matches:
                        # try to find the method
                        # simplest is just to print the route and let human/AI check
                        route = route.split('?')[0]
                        frontend_routes.append((path, route))

# Normalize backend routes (remove dynamic parts like {id})
backend_route_prefixes = []
for br in backend_routes:
    method, path = br.split(" ", 1)
    # just look at prefix before {
    prefix = path.split("{")[0]
    if prefix.endswith("/"): prefix = prefix[:-1]
    if prefix:
        backend_route_prefixes.append(prefix)

# Check which frontend routes do not match ANY backend route prefix
print("=== MISSING ENDPOINTS IN BACKEND ===")
missing_count = 0
for path, route in frontend_routes:
    # route is like /giam-sat/thong-ke
    # remove dynamic part ${id}
    route_prefix = route.split("${")[0]
    if route_prefix.endswith("/"): route_prefix = route_prefix[:-1]
    
    # allow exact matches or prefix matches
    found = False
    for br_prefix in backend_route_prefixes:
        if br_prefix == route_prefix or route_prefix.startswith(br_prefix) or (br_prefix and br_prefix.startswith(route_prefix)):
            found = True
            break
    
    if not found:
        print(f"MISSING: {route} IN {path}")
        missing_count += 1

if missing_count == 0:
    print("All frontend routes seem to exist in backend!")
