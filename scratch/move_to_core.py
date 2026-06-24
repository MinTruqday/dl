import os
import shutil
import re

backend_dir = './backend'
services = []
for item in os.listdir(backend_dir):
    service_path = os.path.join(backend_dir, item)
    if os.path.isdir(service_path) and item not in ['logs', 'tests', 'venv']:
        src_dir = os.path.join(service_path, 'src')
        if os.path.exists(src_dir):
            services.append(item)

# 1. Move src/shared to src/core
for svc in services:
    svc_shared_dir = os.path.join(backend_dir, svc, 'src', 'shared')
    svc_core_dir = os.path.join(backend_dir, svc, 'src', 'core')
    
    if os.path.exists(svc_shared_dir):
        # We need to merge contents into core
        if not os.path.exists(svc_core_dir):
            os.makedirs(svc_core_dir)
        
        for item in os.listdir(svc_shared_dir):
            s = os.path.join(svc_shared_dir, item)
            d = os.path.join(svc_core_dir, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.move(s, d)
                else:
                    # Merge directories
                    for sub_item in os.listdir(s):
                        sub_s = os.path.join(s, sub_item)
                        sub_d = os.path.join(d, sub_item)
                        if not os.path.exists(sub_d):
                            shutil.move(sub_s, sub_d)
            else:
                if not os.path.exists(d):
                    shutil.move(s, d)
        
        shutil.rmtree(svc_shared_dir)

# 2. Update all imports from src.shared to src.core
def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    # Replace 'src.shared' -> 'src.core'
    new_content = new_content.replace('from src.shared', 'from src.core')
    new_content = new_content.replace('import src.shared', 'import src.core')
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    for root, _, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                update_imports(os.path.join(root, file))

print("Moved src/shared to src/core and updated imports.")
