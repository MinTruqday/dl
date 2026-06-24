import os

for root, dirs, files in os.walk("backend"):
    for file in files:
        if file.endswith("mongo_client.py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            content = content.replace("mongo_client = MongoClient()", "mongo = MongoClient()")
            with open(filepath, 'w') as f:
                f.write(content)
