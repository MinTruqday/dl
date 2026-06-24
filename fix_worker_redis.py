with open("backend/worker/src/main.py", "r") as f:
    c = f.read()
c = c.replace("import redis.asyncio as redis", "from src.core.infrastructure.redis_client import redis_client")
c = c.replace("cache = redis.from_url(settings.REDIS_URI, decode_responses=True)", "")
c = c.replace("await cache.ping()", "await redis_client.get('health')")
with open("backend/worker/src/main.py", "w") as f:
    f.write(c)
