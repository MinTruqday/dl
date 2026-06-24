import os
import shutil

backend_dir = './backend'
services = []
for item in os.listdir(backend_dir):
    service_path = os.path.join(backend_dir, item)
    if os.path.isdir(service_path) and item not in ['logs', 'tests', 'venv', 'shared']:
        src_dir = os.path.join(service_path, 'src')
        if os.path.exists(src_dir):
            services.append(item)

def get_all_python_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return files

def get_imports_in_service(svc):
    imports = set()
    svc_dir = os.path.join(backend_dir, svc)
    for fpath in get_all_python_files(svc_dir):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all strings like 'src.core.xxx.yyy'
            import re
            matches = re.findall(r'src\.core\.([a-zA-Z0-9_\.]+)', content)
            for m in matches:
                # m could be 'infrastructure.configuration', etc.
                parts = m.split('.')
                # Record all prefixes
                for i in range(1, len(parts) + 1):
                    imports.add('.'.join(parts[:i]))
    return imports

print("Starting audit and deletion of unused core files...")

for svc in services:
    core_dir = os.path.join(backend_dir, svc, 'src', 'core')
    if not os.path.exists(core_dir):
        continue
        
    used_imports = get_imports_in_service(svc)
    print(f"Service {svc} uses: {used_imports}")
    
    # Check every file/folder in src/core/ against used_imports
    # E.g. file 'circuit.py' -> 'circuit'
    # folder 'infrastructure' -> 'infrastructure'
    
    def walk_and_delete(current_dir, current_module_path):
        if not os.path.exists(current_dir): return
        
        for item in os.listdir(current_dir):
            if item == '__pycache__': continue
            item_path = os.path.join(current_dir, item)
            module_name = item.replace('.py', '') if item.endswith('.py') else item
            
            full_module_path = f"{current_module_path}.{module_name}" if current_module_path else module_name
            
            # Special exceptions: __init__.py
            if module_name == '__init__':
                continue
                
            # If it's a directory, walk inside it first
            if os.path.isdir(item_path):
                walk_and_delete(item_path, full_module_path)
                # If directory is now empty, delete it
                if not os.listdir(item_path) or list(os.listdir(item_path)) == ['__pycache__'] or list(os.listdir(item_path)) == ['__init__.py', '__pycache__']:
                    shutil.rmtree(item_path)
            else:
                # File: check if full_module_path is in used_imports
                if full_module_path not in used_imports:
                    # It's not used, delete it!
                    print(f"Deleting unused {item_path} in {svc}")
                    os.remove(item_path)

    walk_and_delete(core_dir, "")
