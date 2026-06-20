path = "backend/realtime/src/services/message_socket.py"
with open(path, "r") as f:
    content = f.read()

# message_manager is a MessageConnectionManager
content = content.replace("message_manager = ConnectionManager()", "message_manager = MessageConnectionManager()")
with open(path, "w") as f:
    f.write(content)
