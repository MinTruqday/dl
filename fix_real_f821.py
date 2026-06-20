# Fix finance/src/services/purchase.py
path = "backend/finance/src/services/purchase.py"
with open(path, "r") as f: content = f.read()
content = "from core.config import settings\n" + content
with open(path, "w") as f: f.write(content)

# Fix realtime/src/services/message_socket.py
path = "backend/realtime/src/services/message_socket.py"
with open(path, "r") as f: content = f.read()
content = content.replace("ConnectionManager()", "MessageConnectionManager()")
with open(path, "w") as f: f.write(content)

