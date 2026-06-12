import os

target_dirs = [
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/worker',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/signal',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/provision',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/contact',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/content',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compiler',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/authentication',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/finance',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/websocket',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/core',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/collector',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai'
]

replacements = {
    "gặp sự cố": "thất bại",
    "Gặp sự cố": "Thất bại",
    "hoàn tất": "thành công",
    "Hoàn tất": "Thành công"
}

total_files_modified = 0

for d in target_dirs:
    for root, dirs, files in os.walk(d):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                new_content = content
                for k, v in replacements.items():
                    new_content = new_content.replace(k, v)
                
                if new_content != content:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    total_files_modified += 1

print(f"Reverted to thành công / thất bại in {total_files_modified} files.")
