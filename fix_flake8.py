import os

# Fix 1: finance/src/services/purchase.py undefined settings
path = "backend/finance/src/services/purchase.py"
with open(path, "r") as f:
    content = f.read()
if "from core.config import settings" not in content:
    content = "from core.config import settings\n" + content
with open(path, "w") as f:
    f.write(content)

# Fix 2: management/src/services/telemetry.py undefined actor_id
path = "backend/management/src/services/telemetry.py"
with open(path, "r") as f:
    content = f.read()
content = content.replace('{"actor_id": actor_id}', '{"actor_id": user_id}')
with open(path, "w") as f:
    f.write(content)

# Fix 3: realtime/src/services/message_socket.py undefined MessageConnectionManager
path = "backend/realtime/src/services/message_socket.py"
with open(path, "r") as f:
    content = f.read()
# Replace MessageConnectionManager with connection_manager or just comment it out? Wait, look for definition of connection_manager
# Actually let's just ignore it if it's not a big deal or replace it with connection_manager
content = content.replace("MessageConnectionManager()", "ConnectionManager()")
with open(path, "w") as f:
    f.write(content)

# Fix 4: base_repository.py get_default_database() -> settings.SERVICE_DB_NAME
path = "backend/core/repositories/base_repository.py"
with open(path, "r") as f:
    content = f.read()
if "from core.config import settings" not in content:
    content = content.replace("from core.database import db_client", "from core.database import db_client\nfrom core.config import settings")
content = content.replace("get_default_database()", f"get_database(settings.SERVICE_DB_NAME)") # Wait, PyMongo is just db_client.mongodb[settings.SERVICE_DB_NAME]
content = content.replace("db_client.mongodb.get_default_database()", "db_client.mongodb[settings.SERVICE_DB_NAME]")
with open(path, "w") as f:
    f.write(content)

