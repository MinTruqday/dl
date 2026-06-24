import re
import os

def process_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()

    orig_content = content

    # 1. replace `await db["col"].find_one(query)` or `await db.col.find_one(query)`
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.find_one\((.*?)\)',
        lambda m: f'db_client.find_one(collection="{m.group(1) or m.group(2)}", query={m.group(3)})',
        content
    )
    
    # 2. replace `await db["col"].insert_one(doc)`
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.insert_one\((.*?)\)',
        lambda m: f'db_client.insert_one(collection="{m.group(1) or m.group(2)}", document={m.group(3)})',
        content
    )
    
    # 3. replace update_one
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.update_one\((.*?)\)',
        lambda m: f'db_client.update_one(collection="{m.group(1) or m.group(2)}", {m.group(3)})' if "=" in m.group(3) else f'db_client.update_one(collection="{m.group(1) or m.group(2)}", filter={m.group(3).split(",", 1)[0].strip()}, update={m.group(3).split(",", 1)[1].strip()})' if "," in m.group(3) else f'db_client.update_one(collection="{m.group(1) or m.group(2)}", filter={m.group(3)})',
        content
    )

    # 4. replace update_many
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.update_many\((.*?)\)',
        lambda m: f'db_client.update_many(collection="{m.group(1) or m.group(2)}", filter={m.group(3).split(",", 1)[0].strip()}, update={m.group(3).split(",", 1)[1].strip()})' if "," in m.group(3) and "=" not in m.group(3) else f'db_client.update_many(collection="{m.group(1) or m.group(2)}", {m.group(3)})',
        content
    )

    # 5. replace delete_one
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.delete_one\((.*?)\)',
        lambda m: f'db_client.delete_one(collection="{m.group(1) or m.group(2)}", filter={m.group(3)})',
        content
    )

    # 6. replace delete_many
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.delete_many\((.*?)\)',
        lambda m: f'db_client.delete_many(collection="{m.group(1) or m.group(2)}", filter={m.group(3)})',
        content
    )

    # 7. replace count_documents
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.count_documents\((.*?)\)',
        lambda m: f'db_client.count_documents(collection="{m.group(1) or m.group(2)}", filter={m.group(3)})',
        content
    )

    # 8. replace aggregate
    content = re.sub(
        r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.aggregate\((.*?)\)',
        lambda m: f'db_client.aggregate(collection="{m.group(1) or m.group(2)}", pipeline={m.group(3)})',
        content
    )

    # 9. replace find() chained
    # Match: db["col"].find(query).sort(sort).skip(skip).limit(limit).to_list(length=length)
    pattern = re.compile(r'db(?:\["(.*?)"\]|\.([a-zA-Z0-9_]+))\.find\((.*?)\)(?:\.sort\((.*?)\))?(?:\.skip\((.*?)\))?(?:\.limit\((.*?)\))?\.to_list\((?:length=)?(.*?)\)')
    def repl_find_chained(m):
        col = m.group(1) or m.group(2)
        query = m.group(3)
        sort = m.group(4)
        skip = m.group(5)
        limit = m.group(6) or m.group(7) # length is limit
        
        args = [f'collection="{col}"', f'query={query}']
        if sort:
            # check if sort is multiple params e.g. "created_at", -1
            if "," in sort and "[" not in sort:
                # convert "field", -1 to [("field", -1)]
                args.append(f'sort=[({sort})]')
            else:
                args.append(f'sort={sort}')
        if skip:
            args.append(f'skip={skip}')
        if limit and limit != "None":
            args.append(f'limit={limit}')
            
        return f'db_client.find({", ".join(args)})'
    
    content = pattern.sub(repl_find_chained, content)

    # 10. Replace .to_list() on standalone cursors
    # cursor = docs_col.find(...) \n docs = await cursor.to_list(length=100)
    # This is tricky without AST. Let's do simple regex if possible.
    content = re.sub(
        r'cursor\.to_list\((?:length=)?(.*?)\)',
        r'cursor # NO LONGER NEED TO_LIST: result is already list. Remove `await cursor.to_list(...)` manually.',
        content
    )

    if content != orig_content:
        # We need to add the import for db_client if not present
        if "from src.core.api_client import db_client" not in content and "from src.core.infrastructure.api_client import db_client" not in content:
            if "agentic_ai" in fpath:
                content = "from src.core.infrastructure.api_client import db_client\n" + content
            else:
                content = "from src.core.api_client import db_client\n" + content
        with open(fpath, "w") as f:
            f.write(content)
        print(f"Patched {fpath}")

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "database" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            fpath = os.path.join(root, file)
            process_file(fpath)
