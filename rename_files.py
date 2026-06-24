import os

# 1. Rename files
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file == "mongo_client.py":
            old_path = os.path.join(root, file)
            new_path = os.path.join(root, "mongo.py")
            os.rename(old_path, new_path)
        elif file == "queue_client.py":
            old_path = os.path.join(root, file)
            new_path = os.path.join(root, "mq.py")
            os.rename(old_path, new_path)

# 2. Update imports inside files
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            new_content = content.replace("src.core.infrastructure.mongo_client", "src.core.infrastructure.mongo")
            new_content = new_content.replace("src.core.infrastructure.queue_client", "src.core.infrastructure.mq")
            
            if content != new_content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"Updated imports in {filepath}")
