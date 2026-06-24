import os
import re

BACKEND_DIR = "backend"

def fix_mq_lazy_init(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Apply lazy initialization if not already done
    if "def get_client(self):" not in content:
        # replace __init__
        content = re.sub(
            r"def __init__\(self, base_url: str = settings\.QUEUE_URL\):\n\s+self\.base_url = base_url\n\s+self\._client = httpx\.AsyncClient\(base_url=self\.base_url, timeout=10\.0\)",
            """def __init__(self, base_url: str = settings.QUEUE_URL):
        self.base_url = base_url
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._client""",
            content
        )
        
        # fallback if the previous script didn't run properly on some files
        content = re.sub(
            r"def __init__\(self, base_url: str = settings\.QUEUE_URL\):\n\s+self\.base_url = base_url(?!.*self\._client)",
            """def __init__(self, base_url: str = settings.QUEUE_URL):
        self.base_url = base_url
        self._client = None

    def get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._client""",
            content
        )

        # replace self._client.post with self.get_client().post
        content = content.replace(
            "response = await self._client.post(path, json=json_data)",
            "client = self.get_client()\n            response = await client.post(path, json=json_data)"
        )
        
        # replace self._client.get with self.get_client().get
        content = content.replace(
            "response = await self._client.get(path, params=params, timeout=timeout)",
            "client = self.get_client()\n            response = await client.get(path, params=params, timeout=timeout)"
        )

    with open(filepath, "w") as f:
        f.write(content)

def fix_redis_client_silent_failure(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Find the _post method and modify its exception handling
    if 'return None' in content and 'logger.error' not in content.split('def _post')[1][:300]:
        # This targets the specific `except Exception as e:\n            return None` in _post
        content = re.sub(
            r"except Exception as e:\n\s+return None",
            r"""except Exception as e:
            from loguru import logger
            logger.error(f"Redis Cache Server Error at {path}: {e}")
            raise Exception("Cache service unavailable")""",
            content
        )
        
    with open(filepath, "w") as f:
        f.write(content)

def fix_main_shutdown(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    if "def shutdown_event():" not in content:
        shutdown_block = """

@app.on_event("shutdown")
async def shutdown_event():
    try:
        from src.core.infrastructure.redis_client import redis_client
        await redis_client.aclose()
    except Exception:
        pass
    try:
        from src.core.infrastructure.mq import mq
        await mq.aclose()
    except Exception:
        pass
"""
        # Inject at the end of the file
        content += shutdown_block

    with open(filepath, "w") as f:
        f.write(content)


for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        filepath = os.path.join(root, f)
        service_name = root.split('/')[1] if len(root.split('/')) > 1 else ""
        
        if f == "mq.py" and "core/infrastructure" in root:
            fix_mq_lazy_init(filepath)
            print(f"Fixed mq.py in {service_name}")
            
        elif f == "redis_client.py" and "core/infrastructure" in root:
            fix_redis_client_silent_failure(filepath)
            print(f"Fixed redis_client.py in {service_name}")
            
        elif f == "main.py" and "src" in root and "worker" not in root.split('/'): # Wait, it should fix all main.py
            pass
            
        if f == "main.py":
            # Just fix all main.py that have "app = FastAPI"
            with open(filepath, "r") as tmp_f:
                if "app = FastAPI" in tmp_f.read():
                    fix_main_shutdown(filepath)
                    print(f"Fixed main.py in {filepath}")

print("Done fixing phase 2 shared files.")
