import os
import glob
import re

files = glob.glob('backend/**/*.py', recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    if 'settings.' in content and 'core.config' not in content and 'import settings' not in content:
        # We need to add `from core.config import settings`
        # Add it right after other imports
        
        # Find the last import line
        lines = content.split('\n')
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
                
        if last_import_idx != -1:
            lines.insert(last_import_idx + 1, 'from core.config import settings')
        else:
            lines.insert(0, 'from core.config import settings')
            
        with open(file, 'w') as f:
            f.write('\n'.join(lines))
        print(f"Added settings import to {file}")
