import os

services = [d for d in os.listdir("backend") if os.path.isdir(os.path.join("backend", d)) and d != "database" and d != "tests" and d != "logs"]

for srv in services:
    core_path = os.path.join("backend", srv, "src", "core", "infrastructure")
    db_file = os.path.join(core_path, "database.py")
    proxy_file = os.path.join(core_path, "db_client.py")
    
    if os.path.exists(proxy_file):
        os.remove(proxy_file)
        
    core_path_alt = os.path.join("backend", srv, "src", "core")
    proxy_file_alt = os.path.join(core_path_alt, "db_client.py")
    if os.path.exists(proxy_file_alt):
        os.remove(proxy_file_alt)
        
    if os.path.exists(db_file):
        with open(db_file, "r") as f:
            content = f.read()
        
        # Remove ClientProxy
        content = content.replace("from src.core.infrastructure.db_client import ClientProxy\n", "")
        content = content.replace("from src.core.db_client import ClientProxy\n", "")
        content = content.replace("    database.mongodb = ClientProxy()\n", "")
        
        with open(db_file, "w") as f:
            f.write(content)
