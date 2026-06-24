import re
import os

def clean_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()
    orig = content
    
    # Remove _get_db() method
    content = re.sub(r'    @staticmethod\n    def _get_db\(\).*?\n        return database\.mongodb\.get_database\(db_name\)\n', '', content, flags=re.DOTALL)
    
    # Also another variant where it uses get_default_database()
    content = re.sub(r'    @staticmethod\n    def _get_db\(\).*?\n        return database\.mongodb\.get_default_database\(\)\n', '', content, flags=re.DOTALL)
    
    # Remove import database
    # content = re.sub(r'from src\.core\.infrastructure\.database import database\n', '', content)
    
    if orig != content:
        with open(fpath, "w") as f:
            f.write(content)
        print(f"Cleaned {fpath}")

for root, dirs, files in os.walk("backend"):
    if "tests" in root or "logs" in root or "database" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            clean_file(os.path.join(root, file))
