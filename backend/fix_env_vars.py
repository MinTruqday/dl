import os

replacements = {
    'settings.EDITOR_URL': 'settings.EDITOR_URL',
    'settings.MESSAGING_URL': 'settings.MESSAGING_URL',
    'settings.NOTIFICATION_URL': 'settings.NOTIFICATION_URL',
    'settings.MANAGEMENT_URL': 'settings.MANAGEMENT_URL',
    'settings.REALTIME_URL': 'settings.REALTIME_URL'
}

for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Updated {path}")
