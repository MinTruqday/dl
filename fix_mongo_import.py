import os
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                content = f.read()
            if "from src.core.mongo_client import" in content:
                content = content.replace("from src.core.mongo_client import", "from src.core.infrastructure.mongo_client import")
                with open(fpath, "w") as f:
                    f.write(content)
