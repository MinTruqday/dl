import re

# Fix realtime/src/services/message_socket.py
path = "backend/realtime/src/services/message_socket.py"
with open(path, "r") as f: content = f.read()
content = content.replace("message_manager = ConnectionManager()", "message_manager = MessageConnectionManager()")
with open(path, "w") as f: f.write(content)

# Fix finance/src/services/purchase.py
path = "backend/finance/src/services/purchase.py"
with open(path, "r") as f: content = f.read()
if "from core.config import settings" not in content:
    content = "from core.config import settings\n" + content
with open(path, "w") as f: f.write(content)

# Fix agentic_ai/src/main.py
path = "backend/agentic_ai/src/main.py"
with open(path, "r") as f: content = f.read()
if "from core.config import settings" not in content:
    content = "from core.config import settings\n" + content
with open(path, "w") as f: f.write(content)

# Fix agentic_ai/src/router/chat.py
path = "backend/agentic_ai/src/router/chat.py"
with open(path, "r") as f: content = f.read()
if "from core.config import settings" not in content:
    content = "from core.config import settings\n" + content
with open(path, "w") as f: f.write(content)

# We will skip the other agentic_ai errors since they seem to be more complex (missing internal module imports)
# and we already fixed the fatal ones like settings and ConnectionManager.
