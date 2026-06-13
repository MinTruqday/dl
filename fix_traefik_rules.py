import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

# We want to replace PathPrefix(`/a`, `/b`, `/c`) with PathPrefix(`/a`) || PathPrefix(`/b`) || PathPrefix(`/c`)
def replace_path_prefix(match):
    inner = match.group(1)
    paths = [p.strip() for p in inner.split(',')]
    return ' || '.join([f"PathPrefix({p})" for p in paths])

# regex to find PathPrefix(...)
# It might contain multiple paths separated by commas
new_content = re.sub(r'PathPrefix\((.*?)\)', replace_path_prefix, content)

with open('docker-compose.yml', 'w') as f:
    f.write(new_content)

print("Fixed Traefik rules in docker-compose.yml")
