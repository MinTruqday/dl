import os

config_path = "backend/core/config.py"
with open(config_path, "r") as f:
    content = f.read()

# Add SERVICE_DB_NAME
if "SERVICE_DB_NAME:" not in content:
    content = content.replace("MONGODB_DB_NAME: str = os.getenv(\"MONGODB_DB_NAME\")", 
                              "MONGODB_DB_NAME: str = os.getenv(\"MONGODB_DB_NAME\")\n    SERVICE_DB_NAME: str = os.getenv(\"SERVICE_DB_NAME\", os.getenv(\"MONGODB_DB_NAME\"))")
    with open(config_path, "w") as f:
        f.write(content)

database_path = "backend/core/database.py"
with open(database_path, "r") as f:
    content = f.read()

# Change how get_db works? Wait, in dependency.py, it uses `db_client.mongodb[settings.MONGODB_DB_NAME]`.
# So we actually need to change dependency.py and other files using MONGODB_DB_NAME to use SERVICE_DB_NAME!
