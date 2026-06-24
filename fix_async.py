import re
import os

def fix_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()
    orig = content
    content = re.sub(r'async \n\n', '\n', content)
    
    if orig != content:
        with open(fpath, "w") as f:
            f.write(content)

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "database" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))
