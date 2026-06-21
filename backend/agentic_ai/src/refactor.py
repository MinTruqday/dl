import re
import os

router_path = "backend/agentic_ai/src/router/finetune.py"
service_path = "backend/agentic_ai/src/services/finetune.py"

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

# We want to keep the router decorators and definitions, but replace the bodies with calls to the service functions
# It's easier to just generate the router file manually or use regex to replace bodies.
# Let's extract all endpoint definitions.
endpoints = re.findall(r'(@router\.[a-z]+\(.*?\)\nasync def ([a-zA-Z0-9_]+)\((.*?)\):)', router_content, flags=re.DOTALL)

new_router_content = """import asyncio
from fastapi import APIRouter, Query, HTTPException
from src.services import finetune as finetune_service

router = APIRouter(prefix="/tinh-chinh")
"""

for full_match, func_name, args in endpoints:
    # args can be `req: dict`, `dataset_id: str, req: dict`, `user_id: str`
    # We need to construct the call
    # Extract argument names
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
    return await finetune_service.{func_name}({call_args})
"""

with open(router_path, "w") as f:
    f.write(new_router_content)

print("Done refactoring finetune!")
