import re

router_path = "backend/collector/src/router/collector.py"
service_path = "backend/collector/src/services/collector.py"

# Process Service File
with open(service_path, "r") as f:
    service_content = f.read()

# Remove router definition
service_content = re.sub(r'router\s*=\s*APIRouter\(.*?\)\n', '', service_content)

# Remove all @router.* decorators
service_content = re.sub(r'@router\.[a-z]+\(.*?\)\n', '', service_content, flags=re.DOTALL)

with open(service_path, "w") as f:
    f.write(service_content)


# Process Router File
with open(router_path, "r") as f:
    router_content = f.read()

endpoints = re.findall(r'(@router\.[a-z]+\(.*?\)\nasync def ([a-zA-Z0-9_]+)\((.*?)\):)', router_content, flags=re.DOTALL)

new_router_content = """from fastapi import APIRouter
from src.services import collector as collector_service
from src.schemas.collector import CollectionRequest

router = APIRouter()
"""

for full_match, func_name, args in endpoints:
    arg_names = []
    for arg in args.split(","):
        arg = arg.strip()
        if not arg: continue
        arg_name = arg.split(":")[0].split("=")[0].strip()
        arg_names.append(arg_name)
    
    call_args = ", ".join(arg_names)
    
    new_router_content += f"""
{full_match.split('async def')[0].strip()}
async def {func_name}({args}):
    return await collector_service.{func_name}({call_args})
"""

with open(router_path, "w") as f:
    f.write(new_router_content)

print("Done refactoring collector!")
