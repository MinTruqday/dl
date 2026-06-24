import os
import re

BACKEND_DIR = "backend"

MIDDLEWARE_CODE = """
from fastapi import Request
from fastapi.responses import JSONResponse
@app.middleware("http")
async def internal_token_middleware(request: Request, call_next):
    if "/internal/" in request.url.path:
        token = request.headers.get("X-Internal-Token")
        if token != settings.SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid internal token"})
    return await call_next(request)
"""

for root, dirs, files in os.walk(BACKEND_DIR):
    if "main.py" in files:
        filepath = os.path.join(root, "main.py")
        with open(filepath, "r") as f:
            content = f.read()

        # Remove ALL previous occurrences of the middleware and its imports
        content = re.sub(r"from fastapi import Request\nfrom fastapi\.responses import JSONResponse", "", content)
        content = re.sub(r"@app\.middleware\(\"http\"\)\nasync def internal_token_middleware.*?return await call_next\(request\)", "", content, flags=re.DOTALL)
        content = re.sub(r"\n\s*\n", "\n", content) # Clean up empty lines

        # Now cleanly insert it right after app = FastAPI(...)
        if "app = FastAPI" in content:
            parts = content.split("app = FastAPI")
            # find end of line
            first_part = parts[0]
            rest = "app = FastAPI" + parts[1]
            end_of_line = rest.find("\n")
            
            new_content = first_part + rest[:end_of_line] + "\n" + MIDDLEWARE_CODE + rest[end_of_line:]
            
            # Special case cleanup for dangling pass or empty blocks if any
            new_content = re.sub(r"async def startup_event\(\):\s*@app", "async def startup_event():\n    pass\n\n@app", new_content)
            
            with open(filepath, "w") as f:
                f.write(new_content)

