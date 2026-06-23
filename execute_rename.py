import json
import os
import re
import shutil

def process_imports(content, rename_map):
    content = re.sub(r'\bfrom core\.', 'from shared.', content)
    content = re.sub(r'\bimport core\.', 'import shared.', content)
    
    for old_path, new_path in rename_map['files'].items():
        parts = old_path.split('/')
        if 'src' not in parts: continue
        old_module = ".".join(parts[parts.index('src'):])[:-3]
        
        new_parts = new_path.split('/')
        new_module = ".".join(new_parts[new_parts.index('src'):])[:-3]
        
        if old_module != new_module:
            content = re.sub(r'\b' + re.escape(old_module) + r'\b', new_module, content)
    return content

def main():
    with open('rename_map.json', 'r') as f:
        rename_map = json.load(f)

    # 1. Update contents BEFORE renaming anything (so we can find old_paths)
    for old_path in rename_map['files'].keys():
        if not os.path.exists(old_path): continue
        with open(old_path, 'r') as f:
            content = f.read()
        new_content = process_imports(content, rename_map)
        with open(old_path, 'w') as f:
            f.write(new_content)

    # 2. Update Dockerfiles
    for dirpath, dirnames, filenames in os.walk('backend'):
        for filename in filenames:
            if filename == 'Dockerfile':
                path = os.path.join(dirpath, filename)
                with open(path, 'r') as f: content = f.read()
                content = re.sub(r'\bcore/', 'shared/', content)
                for old_dir, new_dir in rename_map['directories'].items():
                    old_base = os.path.basename(old_dir)
                    new_base = os.path.basename(new_dir)
                    content = re.sub(r'\b' + re.escape(old_base) + r'/', new_base + '/', content)
                with open(path, 'w') as f: f.write(content)

    # 3. Rename root directories FIRST (mv backend/agentic_ai backend/intelligence)
    # Wait, some directories might already be partially renamed if the script failed halfway!
    for old_dir, new_dir in rename_map['directories'].items():
        if old_dir == new_dir: continue
        # If old_dir exists and new_dir exists, we might need to merge
        if os.path.exists(old_dir) and not os.path.exists(new_dir):
            os.rename(old_dir, new_dir)
        elif os.path.exists(old_dir) and os.path.exists(new_dir):
            # merge
            for root, dirs, files in os.walk(old_dir):
                for f in files:
                    old_file = os.path.join(root, f)
                    rel_path = os.path.relpath(old_file, old_dir)
                    new_file = os.path.join(new_dir, rel_path)
                    os.makedirs(os.path.dirname(new_file), exist_ok=True)
                    os.rename(old_file, new_file)
            shutil.rmtree(old_dir)

    # 4. Now that root directories are renamed, rename the inner files
    for old_path, new_path in rename_map['files'].items():
        if old_path == new_path: continue
        
        # The file is currently at a hybrid path: new_root + old_inner
        # e.g. old: backend/agentic_ai/src/agents/task_planning.py
        # new: backend/intelligence/src/agents/tasks_plans.py
        # Currently it resides at: backend/intelligence/src/agents/task_planning.py
        
        parts_old = old_path.split('/')
        parts_new = new_path.split('/')
        
        current_path = "/".join([parts_new[0], parts_new[1]] + parts_old[2:])
        
        if os.path.exists(current_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            if current_path != new_path:
                os.rename(current_path, new_path)

    print("Codebase updated and renamed!")

if __name__ == "__main__":
    main()
