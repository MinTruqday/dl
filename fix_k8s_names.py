import os

replacements = {
    "finance-service": "finance",
    "notification-service": "notification",
    "agentic-ai-service": "agentic-ai",
    "collector-service": "collector",
    "editor-service": "editor",
    "authentication-service": "authentication",
    "management-service": "management",
    "realtime-service": "realtime",
    "messaging-service": "messaging",
    "content-service": "content",
    "frontend-service": "frontend",
    "doclib-registry/finance:latest": "doclib_finance:latest",
    # wait, what was the docker image name?
}

for root, _, files in os.walk('k8s'):
    for f in files:
        if f.endswith('.yaml') or f.endswith('.yml'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Fixed {path}")

print("K8s service names fixed.")
