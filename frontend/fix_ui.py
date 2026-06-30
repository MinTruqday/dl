import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Remove standard shadow (not hover:shadow, not shadow-2xl)
    content = re.sub(r'(?<!hover:)\bshadow(?:-sm|-md|-lg)?\b', '', content)
    
    # Clean up multiple spaces in className
    content = re.sub(r' +', ' ', content)

    # Remove <hr />
    content = re.sub(r'<hr[^>]*>', '', content)
    
    # Remove border-b border-[#E8E8ED] from table rows and list items
    content = content.replace('border-b border-[#E8E8ED]', '')
    content = content.replace('border border-[#E8E8ED]', '')
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/app/(main)'):
    for file in files:
        if file.endswith('.tsx'):
            process_file(os.path.join(root, file))
