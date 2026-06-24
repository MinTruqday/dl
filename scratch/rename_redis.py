import os
import re

BACKEND_DIR = "backend"

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        if not f.endswith(".py"):
            continue
            
        filepath = os.path.join(root, f)
        
        # Read content
        with open(filepath, "r") as fp:
            content = fp.read()
            
        original_content = content
        
        # First fix the import inside redis_client.py itself before renaming
        if f == "redis_client.py" and "core/infrastructure" in root:
            content = content.replace("import redis.asyncio as redis", "import redis.asyncio as aioredis")
            content = content.replace("redis.from_url", "aioredis.from_url")
            
        # Replace occurrences
        content = content.replace("src.core.infrastructure.redis_client", "src.core.infrastructure.redis")
        content = re.sub(r"\bredis_client\b", "redis", content)
        
        # If content changed, write it back
        if content != original_content:
            with open(filepath, "w") as fp:
                fp.write(content)
                
        # Rename file if it's redis_client.py
        if f == "redis_client.py" and "core/infrastructure" in root:
            new_filepath = os.path.join(root, "redis.py")
            os.rename(filepath, new_filepath)
            print(f"Renamed {filepath} to {new_filepath}")

print("Redis renaming completed.")
