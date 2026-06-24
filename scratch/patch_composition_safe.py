import re

filepath = "backend/compilation/src/services/composition.py"

with open(filepath, "r") as f:
    content = f.read()

if "from src.core.infrastructure.http_client import http_client" not in content:
    content = content.replace("import httpx", "import httpx\nfrom src.core.infrastructure.http_client import http_client")

# Use regex to match the async with block precisely
content = re.sub(r"async with httpx\.AsyncClient\([^)]*\) as client:", "if True:", content)

# Replace client.method with http_client.method, ensuring it doesn't double replace
content = re.sub(r"\bclient\.post\b", "http_client.post", content)
content = re.sub(r"\bclient\.get\b", "http_client.get", content)
content = re.sub(r"\bclient\.put\b", "http_client.put", content)
content = re.sub(r"\bclient\.delete\b", "http_client.delete", content)

with open(filepath, "w") as f:
    f.write(content)
