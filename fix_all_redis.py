import os
import re

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "websocket" in root or "messaging" in root or "cache" in root:
        continue
    for file in files:
        if not file.endswith(".py"): continue
        fpath = os.path.join(root, file)
        with open(fpath, "r") as f:
            c = f.read()

        changed = False

        if "database.redis" in c:
            # 1. database.py: remove database.redis.close()
            c = re.sub(r'^\s*if database\.redis:\n\s*await database\.redis\.close\(\)', '', c, flags=re.MULTILINE)
            c = re.sub(r'^\s*if hasattr\(database, "redis"\) and database\.redis:\n\s*await database\.redis\.close\(\)', '', c, flags=re.MULTILINE)
            c = re.sub(r'^\s*await database\.redis\.close\(\)', '', c, flags=re.MULTILINE)
            
            # replace database.redis with redis_client
            c = c.replace('hasattr(database, "redis") and database.redis', 'redis_client')
            c = c.replace('database.redis', 'redis_client')
            
            # add import if not there
            if "redis_client" in c and "from src.core.infrastructure.redis_client import redis_client" not in c:
                c = "from src.core.infrastructure.redis_client import redis_client\n" + c
            
            changed = True

        if changed:
            with open(fpath, "w") as f:
                f.write(c)

