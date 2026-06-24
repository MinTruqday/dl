import os
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file == "mongo_client.py":
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                content = f.read()
            content = content.replace("db_client =", "mongo_client =")
            with open(fpath, "w") as f:
                f.write(content)

        # Also fix the import error: `from src.core.infrastructure.mongo_client import mongo_client`
        # Wait, if `db_client` was used in `from src.core.infrastructure.mongo_client import db_client`
        # my script rename_mongo_client.py didn't rename the import name either!
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            with open(fpath, "r") as f:
                content = f.read()
            if "import db_client" in content:
                content = content.replace("import db_client", "import mongo_client")
            if "from src.core.infrastructure.mongo_client import db_client" in content:
                content = content.replace("from src.core.infrastructure.mongo_client import db_client", "from src.core.infrastructure.mongo_client import mongo_client")
            with open(fpath, "w") as f:
                f.write(content)
