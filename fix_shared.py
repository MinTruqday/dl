import os
import re

SHARED_RENAMES = {
    "api_response.py": "responses.py",
    "file_storage.py": "storage.py",
    "system_dependency.py": "dependencies.py",
    "system_middleware.py": "middlewares.py",
    "infrastructure/app_config.py": "infrastructure/config.py",
    "infrastructure/database_client.py": "infrastructure/database.py",
    "security/role_based_access.py": "security/access_control.py"
}

CONFIG_RENAMES = {
    "INTELLIGENCE_URL": "INTELLIGENCE_URL",
    "WORKSPACE_URL": "WORKSPACE_URL",
    "INGESTION_URL": "INGESTION_URL",
    "CONVERSATIONS_URL": "CONVERSATIONS_URL",
    "BILLING_URL": "BILLING_URL",
    "ALERTS_URL": "ALERTS_URL",
    "ADMINISTRATION_URL": "ADMINISTRATION_URL",
    "IDENTITY_URL": "IDENTITY_URL",
    "DOCUMENTS_URL": "DOCUMENTS_URL",
    "LIVE_EVENTS_URL": "LIVE_EVENTS_URL",
    "SHARED_URL": "SHARED_URL",
    "SHARED_BACKEND_URL": "SHARED_BACKEND_URL"
}

HOST_RENAMES = {
    "http://intelligence:8000": "http://intelligence:8000",
    "http://workspace:8000": "http://workspace:8000",
    "http://ingestion:8000": "http://ingestion:8000",
    "http://conversations:8000": "http://conversations:8000",
    "http://billing:8000": "http://billing:8000",
    "http://alerts:8000": "http://alerts:8000",
    "http://administration:8000": "http://administration:8000",
    "http://identity:8000": "http://identity:8000",
    "http://documents:8000": "http://documents:8000",
    "ws://live_events:8000": "ws://live_events:8000",
}

def process_content(content):
    # Fix import paths
    for old, new in SHARED_RENAMES.items():
        old_mod = old.replace("/", ".")[:-3]
        new_mod = new.replace("/", ".")[:-3]
        content = re.sub(r'\bshared\.' + re.escape(old_mod) + r'\b', 'shared.' + new_mod, content)
        
    # Fix settings attributes
    for old, new in CONFIG_RENAMES.items():
        content = re.sub(r'\b' + old + r'\b', new, content)
        
    # Fix URLs in .env
    for old, new in HOST_RENAMES.items():
        content = content.replace(old, new)
        
    return content

def main():
    # 1. Update all files (.py, .env, .ts, .tsx)
    for root_dir in ['.']:
        for root, dirs, files in os.walk(root_dir):
            if 'node_modules' in root or '.git' in root or 'venv' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.ts', '.tsx', '.env', '.env.local', 'docker-compose.yml')):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        new_content = process_content(content)
                        if new_content != content:
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                    except Exception as e:
                        pass # skip binary files or encoding errors

    # 2. Rename files in shared/
    shared_path = 'backend/shared'
    for old, new in SHARED_RENAMES.items():
        old_path = os.path.join(shared_path, old)
        new_path = os.path.join(shared_path, new)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)

if __name__ == "__main__":
    main()
