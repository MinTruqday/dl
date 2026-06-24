with open("backend/collection/src/core/database.py", "r") as f:
    content = f.read()

content = content.replace("from src.core.db_client import ClientProxy", "")
content = content.replace("database.mongodb = ClientProxy()", "")
with open("backend/collection/src/core/database.py", "w") as f:
    f.write(content)
