import os
import re

backend_dir = './backend'
services = []
for item in os.listdir(backend_dir):
    service_path = os.path.join(backend_dir, item)
    if os.path.isdir(service_path) and item not in ['logs', 'tests', 'venv']:
        src_dir = os.path.join(service_path, 'src')
        if os.path.exists(src_dir):
            services.append(item)

def to_camel_case(snake_str):
    if snake_str.endswith('s'):
        snake_str = snake_str[:-1] # rudimentary singularization
    components = snake_str.split('_')
    return ''.join(x.title() for x in components) + "Repository"

def to_singular(snake_str):
    if snake_str.endswith('s'):
        return snake_str[:-1]
    return snake_str

# 1. Find all repository usages and methods per collection per service
for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    repo_usage = {} # collection_name -> set of methods used
    
    # regex to find: XXXRepository.get("collection_name").method_name
    pattern = re.compile(r'[A-Za-z]+Repository\.get\("([a-z_]+)"\)\.([a-z_]+)')
    
    py_files = []
    for root, _, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
                
    for fpath in py_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        matches = pattern.findall(content)
        for coll_name, method_name in matches:
            if coll_name not in repo_usage:
                repo_usage[coll_name] = set()
            repo_usage[coll_name].add(method_name)
            
    if not repo_usage:
        continue
        
    print(f"Service {svc} needs repos: {repo_usage}")
    
    # Create specific repositories in src/repositories/
    repos_dir = os.path.join(svc_dir, 'src', 'repositories')
    os.makedirs(repos_dir, exist_ok=True)
    
    for coll_name, methods in repo_usage.items():
        class_name = to_camel_case(coll_name)
        file_name = to_singular(coll_name) + ".py"
        repo_file_path = os.path.join(repos_dir, file_name)
        
        # Build the repository class
        lines = [
            "from typing import Optional, Dict, Any, List",
            "from src.core.infrastructure.database import database",
            "from src.core.infrastructure.configuration import settings",
            "",
            f"class {class_name}:",
            "    @staticmethod",
            "    def _get_db():",
            "        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'",
            "        return database.mongodb.get_database(db_name)",
            ""
        ]
        
        for method in methods:
            if method == 'find_one':
                lines.append("    @classmethod")
                lines.append(f"    async def find_one(cls, *args, **kwargs):")
                lines.append(f"        return await cls._get_db()['{coll_name}'].find_one(*args, **kwargs)")
            elif method == 'find':
                lines.append("    @classmethod")
                lines.append(f"    def find(cls, *args, **kwargs):")
                lines.append(f"        return cls._get_db()['{coll_name}'].find(*args, **kwargs)")
            elif method in ['insert_one', 'insert_many', 'update_one', 'update_many', 'delete_one', 'delete_many', 'count_documents']:
                lines.append("    @classmethod")
                lines.append(f"    async def {method}(cls, *args, **kwargs):")
                lines.append(f"        return await cls._get_db()['{coll_name}'].{method}(*args, **kwargs)")
            elif method == 'aggregate':
                lines.append("    @classmethod")
                lines.append(f"    def aggregate(cls, *args, **kwargs):")
                lines.append(f"        return cls._get_db()['{coll_name}'].aggregate(*args, **kwargs)")
            lines.append("")
            
        with open(repo_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        # Replace occurrences in all python files
        # We need to replace `XXXRepository.get("coll_name")` with `ClassName`
        # and add the import `from src.repositories.file_name import ClassName`
        replace_pattern = re.compile(rf'[A-Za-z]+Repository\.get\("{coll_name}"\)')
        
        for fpath in py_files:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if replace_pattern.search(content):
                # We need to add the import if it's not there
                import_stmt = f"from src.repositories.{to_singular(coll_name)} import {class_name}"
                new_content = replace_pattern.sub(class_name, content)
                
                # Insert import at the top after other imports, roughly
                if import_stmt not in new_content:
                    lines = new_content.split('\n')
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_idx = i + 1
                    lines.insert(insert_idx, import_stmt)
                    new_content = '\n'.join(lines)
                
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

    # Finally, delete the generic src/core/repositories/database.py
    core_repo_file = os.path.join(svc_dir, 'src', 'core', 'repositories', 'database.py')
    if os.path.exists(core_repo_file):
        os.remove(core_repo_file)
        print(f"Deleted {core_repo_file}")

# Clean up any leftover imports of XXXRepository
for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    for root, _, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                fpath = os.path.join(root, file)
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(r'from src\.core\.repositories\.database import [A-Za-z]+Repository\n', '', content)
                
                if new_content != content:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
