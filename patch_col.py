import os
core_path = "backend/collection/src/core"
db_file = os.path.join(core_path, "database.py")
if os.path.exists(db_file):
    # Create db_client.py
    with open("patch_db.py", "r") as f:
        code = f.read()
    proxy_code = code.split('proxy_code = """\n')[1].split('"""\n\nservices')[0]
    
    with open(os.path.join(core_path, "db_client.py"), "w") as f:
        f.write(proxy_code)
    
    with open(db_file, "r") as f:
        content = f.read()
    
    if "from motor.motor_asyncio import AsyncIOMotorClient" in content:
        content = content.replace("from motor.motor_asyncio import AsyncIOMotorClient", "from src.core.db_client import ClientProxy")
        content = content.replace("AsyncIOMotorClient(settings.MONGODB_URI, maxPoolSize=100)", "ClientProxy()")
        
        with open(db_file, "w") as f:
            f.write(content)
        print(f"Patched {db_file}")
