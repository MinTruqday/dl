import re

filepath = "backend/compilation/src/services/composition.py"

with open(filepath, "r") as f:
    content = f.read()

# Replace async with httpx.AsyncClient(...) as client: block
# with: response = await http_client.post(...)

if "from src.core.infrastructure.http_client import http_client" not in content:
    content = content.replace("import httpx", "import httpx\nfrom src.core.infrastructure.http_client import http_client")

pattern = re.compile(r"async with httpx\.AsyncClient\([^)]*\) as client:\n\s+([^\n]+)", re.DOTALL)

def replacer(match):
    inner = match.group(1).strip()
    return inner.replace("client.", "http_client.")

content = re.sub(r"async with httpx\.AsyncClient\([^)]*\) as client:\n\s+([^\n]+)", replacer, content)

# But wait, the inner part can be multiple lines!
# Instead of regex, let's just do simple string replacements.

content = re.sub(r"async with httpx\.AsyncClient\([^)]*\) as client:", "if True:", content)
content = content.replace("client.post", "http_client.post")
content = content.replace("client.get", "http_client.get")
content = content.replace("client.put", "http_client.put")
content = content.replace("client.delete", "http_client.delete")

with open(filepath, "w") as f:
    f.write(content)
