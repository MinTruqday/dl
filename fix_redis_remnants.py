import os
for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "websocket" in root or "messaging" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                c = f.read()
            if "database.redis" in c or "redis" in c:
                # Need to be careful.
                pass
