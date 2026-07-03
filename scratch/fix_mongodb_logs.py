import os
import glob
import re

backend_dir = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend'
files = glob.glob(f"{backend_dir}/**/*.py", recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()

    # Replace "Database" with "MongoDB" in common log strings
    # But only inside quotes.
    if 'Database"' in content or 'Database' in content:
        # Let's just do a simple replacement for the specific log strings we know exist:
        new_content = content.replace('thiếu kết nối Database', 'thiếu kết nối MongoDB')
        new_content = new_content.replace('chỉ mục Database', 'chỉ mục MongoDB')
        new_content = new_content.replace('chỉ mục cho Database', 'chỉ mục cho MongoDB')
        new_content = new_content.replace('truy vấn Database', 'truy vấn MongoDB')
        new_content = new_content.replace('kết nối Database', 'kết nối MongoDB')
        new_content = new_content.replace('từ Database', 'từ MongoDB')
        
        # If there are any remaining isolated "Database" in logs, we could just replace them.
        # But we must be careful not to replace class names like `DatabaseInfrastructure`.
        # The strings above cover almost all the logs. Let's write them back.
        
        if new_content != content:
            with open(file, 'w') as f:
                f.write(new_content)
            print(f"Updated logs in {file}")

print("Done")
