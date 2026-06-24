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
    if snake_str == 'drm': return 'DRM'
    if snake_str == 'agentic_ai': return 'AgenticAIRepository'
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)

for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    repo_file = os.path.join(svc_dir, 'src', 'core', 'repositories', 'database.py')
    
    if not os.path.exists(repo_file):
        continue
        
    class_name = to_camel_case(svc)
    if not class_name.endswith('Repository'):
        class_name += 'Repository'
        
    print(f"Service {svc}: renaming BaseRepository to {class_name}")
    
    # Iterate all python files in the service and replace BaseRepository -> class_name
    for root, _, files in os.walk(svc_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content.replace('BaseRepository', class_name)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
print("Renamed repositories successfully.")
