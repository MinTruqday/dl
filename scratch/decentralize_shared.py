import os
import shutil

backend_dir = './backend'
shared_dir = os.path.join(backend_dir, 'shared')

# Lấy danh sách các service hợp lệ (các thư mục có src/)
services = []
for item in os.listdir(backend_dir):
    service_path = os.path.join(backend_dir, item)
    if os.path.isdir(service_path) and item not in ['shared', 'logs', 'tests', 'venv']:
        src_dir = os.path.join(service_path, 'src')
        if os.path.exists(src_dir):
            services.append(item)

print(f"Decentralizing shared folder into {len(services)} services: {services}")

# 1. Copy shared folder into each service's src/shared
for svc in services:
    svc_shared_dir = os.path.join(backend_dir, svc, 'src', 'shared')
    if os.path.exists(svc_shared_dir):
        shutil.rmtree(svc_shared_dir)
    
    # Copy shared to src/shared
    shutil.copytree(shared_dir, svc_shared_dir)
    print(f"Copied shared to {svc_shared_dir}")

# 2. Update imports in all python files
import re

def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    # Replace 'from shared.' -> 'from src.shared.'
    new_content = re.sub(r'^from shared\.', 'from src.shared.', new_content, flags=re.MULTILINE)
    # Replace 'from shared import' -> 'from src.shared import'
    new_content = re.sub(r'^from shared import', 'from src.shared import', new_content, flags=re.MULTILINE)
    # Replace 'import shared.' -> 'import src.shared.'
    new_content = re.sub(r'^import shared\.', 'import src.shared.', new_content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated imports in {file_path}")

for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    for root, _, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                update_imports(os.path.join(root, file))

# 3. Delete the global shared folder
shutil.rmtree(shared_dir)
print(f"Deleted global shared directory: {shared_dir}")
