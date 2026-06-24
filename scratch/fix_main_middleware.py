import os
BACKEND_DIR = "backend"

for root, dirs, files in os.walk(BACKEND_DIR):
    if "main.py" in files:
        filepath = os.path.join(root, "main.py")
        with open(filepath, "r") as f:
            content = f.read()
            
        if "@app.middleware" in content and "app = FastAPI" in content:
            # Find the index of app = FastAPI
            app_def_idx = content.find("app = FastAPI")
            middleware_idx = content.find("@app.middleware")
            
            if middleware_idx < app_def_idx:
                print(f"Fixing {filepath}")
                # We need to move the middleware after app = FastAPI
                # The middleware code I added was:
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
                content = content.replace(middleware_code, "")
                
                # Now we need to append it after app = FastAPI
                # Find the end of the app = FastAPI line
                app_line_end = content.find("\n", app_def_idx)
                
                new_content = content[:app_line_end+1] + middleware_code + content[app_line_end+1:]
                
                with open(filepath, "w") as f:
                    f.write(new_content)
