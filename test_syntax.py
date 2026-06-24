import ast
import os

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "database" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                content = f.read()
            try:
                ast.parse(content)
            except SyntaxError as e:
                print(f"Error in {fpath}:{e.lineno}")
                lines = content.split('\n')
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 3)
                for i in range(start, end):
                    prefix = ">> " if i == e.lineno - 1 else "   "
                    print(f"{prefix}{i+1}: {lines[i]}")
                print("-" * 40)
