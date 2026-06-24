import re
import os

def clean_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()
    orig = content

    # 1. Remove `, db=db` or `db=db, `
    content = re.sub(r',\s*db=db', '', content)
    content = re.sub(r'db=db\s*,', '', content)
    content = re.sub(r'db=db', '', content)

    # 2. Remove `, db=None` or `db=None, `
    content = re.sub(r',\s*db=None', '', content)
    content = re.sub(r'db=None\s*,', '', content)
    content = re.sub(r'db=None', '', content)

    # 3. Remove `db = database.mongodb.get_default_database()`
    content = re.sub(r'db\s*=\s*database\.mongodb\.get_default_database\(\)', '', content)
    
    # 4. Remove `if db is None:` followed by nothing (can cause SyntaxError)
    # Actually, let's just replace the whole block
    content = re.sub(r'if db is None:\s+db\s*=\s*database\.mongodb\.get_default_database\(\)', '', content)
    content = re.sub(r'if db is None:\s+db\s*=\s*get_db\(\)', '', content)

    # 5. Remove `db = get_db()`
    content = re.sub(r'db\s*=\s*get_db\(\)', '', content)
    
    # 6. Remove `def get_db(): ... return ...`
    content = re.sub(r'def get_db\(\):.*?\n\s+return.*?\n', '', content, flags=re.DOTALL)
    
    # 7. There might be some dangling `if db is None:\n\s+pass` if we aren't careful, but since we removed `db=None` from signature, `db` is undefined anyway.
    content = re.sub(r'if db is None:\n\s+', '', content)
    
    if orig != content:
        with open(fpath, "w") as f:
            f.write(content)
        print(f"Cleaned db kwargs in {fpath}")

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "database" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            clean_file(os.path.join(root, file))
