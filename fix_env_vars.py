import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

services = ['finance', 'notification', 'agentic_ai', 'collector', 'editor', 'authentication', 'management', 'realtime', 'messaging', 'content']

lines = content.split('\n')
new_lines = []

in_service = None
for line in lines:
    new_lines.append(line)
    
    match = re.match(r'^  ([a-z_]+):', line)
    if match:
        svc = match.group(1)
        if svc in services:
            in_service = svc
    
    if in_service and re.match(r'^    environment:', line):
        db_name = f"doclib_{in_service}"
        new_lines.append(f"      - SERVICE_DB_NAME={db_name}")
        in_service = None

with open('docker-compose.yml', 'w') as f:
    f.write('\n'.join(new_lines))

print("docker-compose.yml updated with SERVICE_DB_NAME!")
