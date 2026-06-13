import os
import glob

files = glob.glob('backend/**/*.py', recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    if ('settings.DEFAULT_PAGE_LIMIT' in content or 'settings.MAX_PAGE_LIMIT' in content) and not content.startswith('from core.config import settings'):
        lines = content.split('\n')
        # check if it's already imported at the top level
        has_top_import = False
        for line in lines:
            if line.startswith('from core.config import settings'):
                has_top_import = True
                break
            if line.startswith('def ') or line.startswith('class '):
                break # stop checking when hitting functions/classes
                
        if not has_top_import:
            # We need to add it at the top
            lines.insert(0, 'from core.config import settings')
            with open(file, 'w') as f:
                f.write('\n'.join(lines))
            print(f"Fixed {file}")
