import os
import glob

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'Query(' in content and 'from fastapi import' in content and 'Query' not in content[:content.find('Query(')]:
        # Need to add Query to fastapi import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from fastapi import ') and 'Query' not in line:
                lines[i] = line + ', Query'
                break
        else:
            # no from fastapi import found or not easily modifiable
            # just insert it after the last import
            for i, line in enumerate(lines):
                if not line.startswith('import ') and not line.startswith('from '):
                    lines.insert(i, 'from fastapi import Query')
                    break
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        print(f"Fixed {filepath}")
    elif 'Query(' in content and 'from fastapi import ' not in content:
        # just add it at the top
        lines = content.split('\n')
        lines.insert(0, 'from fastapi import Query')
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        print(f"Fixed {filepath}")

for filepath in glob.glob('backend/**/*.py', recursive=True):
    process_file(filepath)
