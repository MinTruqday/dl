import re

with open("backend/contact/src/api/message.py", "r") as f:
    content = f.read()

# Fix the dictionary syntax error
pattern = re.compile(r'json\.dumps\(\{"receiver_id": \'data\': (.*?)\}, (.*?), \*\*\{\'type\': \'(.*?)\'\}\)')
content = pattern.sub(r'json.dumps({"receiver_id": \2, "data": \1, "type": "\3"})', content)

# Fix indentation on line 128
lines = content.split('\n')
for i, line in enumerate(lines):
    if "if db_client.redis:" in line and "await db_client.redis.publish" in lines[i+1] and lines[i+1].startswith("        await"):
        lines[i+1] = "    " + lines[i+1]

with open("backend/contact/src/api/message.py", "w") as f:
    f.write('\n'.join(lines))
