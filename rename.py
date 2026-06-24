import os
import glob

def replace_in_file(filepath, replacements):
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, does not exist.")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# docker-compose.yml
replace_in_file('docker-compose.yml', {
    'MESSAGE_URL=${MESSAGE_URL}': 'MESSAGING_URL=${MESSAGING_URL}',
    '  message:': '  messaging:',
    './message/Dockerfile': './messaging/Dockerfile',
    'container_name: doclib_message': 'container_name: doclib_messaging',
    'SERVICE_DB_NAME=doclib_message': 'SERVICE_DB_NAME=doclib_messaging',
    './backend/message/src:/app/src': './backend/messaging/src:/app/src',
    './backend/logs/messaging:/app/logs': './backend/logs/messaging:/app/logs', # already correct
})

# .env
replace_in_file('.env', {
    'MESSAGE_URL=http://message:8000': 'MESSAGING_URL=http://messaging:8000',
    'MESSAGE_URL': 'MESSAGING_URL'
})

# k8s
k8s_message = 'k8s/apps/message.yaml'
k8s_messaging = 'k8s/apps/messaging.yaml'
if os.path.exists(k8s_message):
    os.rename(k8s_message, k8s_messaging)
    print(f"Renamed {k8s_message} to {k8s_messaging}")

replace_in_file(k8s_messaging, {
    'name: message-deployment': 'name: messaging-deployment',
    'app: message': 'app: messaging',
    'name: message': 'name: messaging',
    'image: doclib-registry/message:latest': 'image: doclib-registry/messaging:latest'
})

replace_in_file('k8s/kustomization.yaml', {
    'apps/message.yaml': 'apps/messaging.yaml'
})

replace_in_file('k8s/ingress/ingress.yaml', {
    'name: message': 'name: messaging'
})

# config.py in all backend services
for filepath in glob.glob('backend/*/src/core/infrastructure/configuration.py'):
    replace_in_file(filepath, {
        'MESSAGE_URL: str = os.getenv("MESSAGE_URL")': 'MESSAGING_URL: str = os.getenv("MESSAGING_URL")'
    })

print("Done renaming.")
