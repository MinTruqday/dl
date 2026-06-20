import os

files_to_fix = [
    "backend/core/database.py",
    "backend/core/dependency.py",
    "backend/authentication/src/repositories/auth_repository.py"
]

for path in files_to_fix:
    with open(path, "r") as f:
        content = f.read()
    
    content = content.replace("settings.MONGODB_DB_NAME", "settings.SERVICE_DB_NAME")
    # Also fix db_client.settings.MONGODB_DB_NAME if it exists
    content = content.replace("db_client.settings.SERVICE_DB_NAME", "settings.SERVICE_DB_NAME")
    
    with open(path, "w") as f:
        f.write(content)

print("MONGODB_DB_NAME replaced with SERVICE_DB_NAME!")
