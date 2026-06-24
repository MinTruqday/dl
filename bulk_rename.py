import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # 1. Rename mongo_client -> mongo
    content = content.replace("from src.core.infrastructure.database_client import mongo_client", "from src.core.infrastructure.database_client import mongo")
    # Some places might import it with 'as'
    content = content.replace("import mongo_client", "import mongo")
    # Replace usages: mongo_client. -> mongo.
    content = re.sub(r'\bmongo_client\.', 'mongo.', content)
    # Inside database_client.py
    if filepath.endswith("database_client.py"):
        content = content.replace("mongo_client = DatabaseAPIClient()", "mongo = DatabaseAPIClient()")

    # 2. Rename queue_client -> mq
    content = content.replace("from src.core.infrastructure.queue_client import queue_client", "from src.core.infrastructure.queue_client import mq")
    content = content.replace("from src.core.infrastructure.queue_client import queue_client as mq_client", "from src.core.infrastructure.queue_client import mq")
    # Replace usages: queue_client. -> mq.
    content = re.sub(r'\bqueue_client\.', 'mq.', content)
    # Replace old aliases if any: mq_client. -> mq.
    content = re.sub(r'\bmq_client\.', 'mq.', content)
    # Inside queue_client.py
    if filepath.endswith("queue_client.py"):
        content = content.replace("queue_client = QueueAPIClient()", "mq = QueueAPIClient()")

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

# Process all .py files in backend/
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            process_file(filepath)
