import re

with open("untranslated.txt", "r") as f:
    lines = f.readlines()

paths = set()
for line in lines:
    if "---" in line or not line.strip():
        continue
    # Extract the route path or prefix
    if "prefix=" in line:
        match = re.search(r"prefix=(.*)", line)
        if match:
            paths.add(match.group(1).strip())
    else:
        match = re.search(r" (/[^\n]*)", line)
        if match:
            # We add exactly what was matched
            paths.add(match.group(1).strip())

# Print them out clearly
for p in sorted(paths):
    print(p)
