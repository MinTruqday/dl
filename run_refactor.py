import os
import re

def process_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()
    orig = content
    
    # Simple regex replacing `db["col"].find_one(query)` with `await db_client.find_one("col", query)`
    # where db is anything that ends with db or _db() or collection or docs_col
    
    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.find_one\((.*?)\)', 
                     lambda m: f'db_client.find_one("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.insert_one\((.*?)\)', 
                     lambda m: f'db_client.insert_one("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.update_one\((.*?)\)', 
                     lambda m: f'db_client.update_one("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.delete_one\((.*?)\)', 
                     lambda m: f'db_client.delete_one("{m.group(2) or m.group(3)}", {m.group(4)})', content)
                     
    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.delete_many\((.*?)\)', 
                     lambda m: f'db_client.delete_many("{m.group(2) or m.group(3)}", {m.group(4)})', content)                     

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.update_many\((.*?)\)', 
                     lambda m: f'db_client.update_many("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.aggregate\((.*?)\)', 
                     lambda m: f'db_client.aggregate("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.count_documents\((.*?)\)', 
                     lambda m: f'db_client.count_documents("{m.group(2) or m.group(3)}", {m.group(4)})', content)

    # For find() with chaining: we replace it with a QueryBuilder syntax
    # e.g. db["users"].find(query).sort(...).limit(...) -> db_client.query("users").filter(query).sort(...).limit(...)
    
    def repl_find(m):
        col = m.group(2) or m.group(3)
        return f'db_client.query("{col}").filter({m.group(4)})'
    
    content = re.sub(r'([a-zA-Z0-9_\(\)\.]+)(?:\[["\'](.*?)["\']\]|\.([a-zA-Z0-9_]+))\.find\((.*?)\)', repl_find, content)

    # Also replace .to_list(length=...) with .execute()
    content = re.sub(r'\.to_list\((.*?)\)', r'.execute()', content)
    
    if orig != content:
        # Add import if needed
        if "from src.core.infrastructure.api_client import db_client" not in content and "from src.core.api_client import db_client" not in content:
            if "agentic_ai" in fpath or "collection" in fpath:
                content = "from src.core.api_client import db_client\n" + content
            else:
                content = "from src.core.infrastructure.api_client import db_client\n" + content
                
        with open(fpath, "w") as f:
            f.write(content)
        print(f"Refactored {fpath}")

for root, dirs, files in os.walk("backend"):
    if "database" in root or "tests" in root or "logs" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
