import os
import re

# 1. Update session.py in authentication
session_py = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/authentication/src/api/session.py"
with open(session_py, "r") as f:
    session_content = f.read()
# Replace hardcoded Traefik URL
session_content = re.sub(r'http://doclib_traefik:8000/su-dung', r'{settings.USAGE_URL}', session_content)
with open(session_py, "w") as f:
    f.write(session_content)

# 2. Update management and worker config
for service in ["management", "worker"]:
    config_py = f"/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/{service}/src/core/infrastructure/configuration.py"
    with open(config_py, "r") as f:
        config_content = f.read()
    
    config_content = re.sub(r'MONGO_URL:\s*str\s*=\s*os\.getenv\("MONGO_URL",\s*"[^"]+"\)', 'MONGO_URL: str = os.getenv("MONGO_URL")', config_content)
    config_content = re.sub(r'QUEUE_URL:\s*str\s*=\s*os\.getenv\("QUEUE_URL",\s*"[^"]+"\)', 'QUEUE_URL: str = os.getenv("QUEUE_URL")', config_content)
    config_content = re.sub(r'CACHE_URL:\s*str\s*=\s*os\.getenv\("CACHE_URL",\s*"[^"]+"\)', 'CACHE_URL: str = os.getenv("CACHE_URL")', config_content)
    
    with open(config_py, "w") as f:
        f.write(config_content)

# 3. Update cloud migrate.py
migrate_py = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/cloud/src/migrate.py"
with open(migrate_py, "r") as f:
    migrate_content = f.read()
migrate_content = migrate_content.replace('os.environ.get("MONGODB_URI", "mongodb://mongodb:27017")', 'os.environ.get("MONGODB_URI")')
with open(migrate_py, "w") as f:
    f.write(migrate_content)

# 4. Update collection storage.py
storage_py = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/collection/src/core/storage.py"
with open(storage_py, "r") as f:
    storage_content = f.read()
storage_content = storage_content.replace('settings.MINIO_ENDPOINT or "minio:9000"', 'settings.MINIO_ENDPOINT')
with open(storage_py, "w") as f:
    f.write(storage_content)

# 5. Add to .env
env_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/.env"
with open(env_path, "r") as f:
    env_content = f.read()

if "MONGO_URL=" not in env_content:
    urls_to_add = "\n# INTERNAL_UIS\nMONGO_URL=http://doclib_database:8800/co-so-du-lieu\nQUEUE_URL=http://doclib_queue:8802/hang-doi\nCACHE_URL=http://doclib_cache:8801\n"
    env_content = env_content + urls_to_add
    with open(env_path, "w") as f:
        f.write(env_content)

print("[x] Cleaned up hardcoded URLs")
