import os
import re

BACKEND_DIR = "backend"

def add_header_to_http_client(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    if "X-Internal-Token" not in content:
        content = content.replace(
            "async def request(self, method: str, url: str, **kwargs):",
            """async def request(self, method: str, url: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["X-Internal-Token"] = settings.SECRET_KEY
        kwargs["headers"] = headers"""
        )
        with open(filepath, "w") as f:
            f.write(content)

def add_middleware_to_main(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    if "internal_token_middleware" not in content:
        middleware_code = """
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
        content = content.replace("app = FastAPI(", middleware_code + "\napp = FastAPI(")
        with open(filepath, "w") as f:
            f.write(content)

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        filepath = os.path.join(root, f)
        if f == "http_client.py":
            add_header_to_http_client(filepath)
        elif f == "main.py":
            with open(filepath, "r") as tmp_f:
                if "app = FastAPI" in tmp_f.read():
                    add_middleware_to_main(filepath)

print("Added zero trust middleware and headers.")
