import os
import re
import subprocess

d = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/features/editor/components'
files = [f for f in os.listdir(d) if f.startswith('DocLib')]

props_to_fix = [
    'opacity', 'scale', 'format', 'color', 'styleId', 'style', 'width', 
    'type', 'borderWidth', 'borderStyle', 'borderColor', 'bgColor', 
    'macroId', 'shape', 'fill', 'stroke', 'float', 'position', 'label'
]

for f in files:
    filepath = os.path.join(d, f)
    
    # Get the commit where this file was added
    try:
        cmd = ['git', 'log', '--diff-filter=A', '--format=%H', '-1', '--', f]
        result = subprocess.run(cmd, cwd=d, capture_output=True, text=True, check=True)
        first_commit = result.stdout.strip()
    except Exception:
        continue
        
    if not first_commit:
        continue

    # Get the file content at that commit
    try:
        # We need the path relative to git root
        rel_path = f"frontend/features/editor/components/{f}"
        cmd2 = ['git', 'show', f'{first_commit}:{rel_path}']
        result2 = subprocess.run(cmd2, cwd=d, capture_output=True, text=True, check=True)
        old_content = result2.stdout
    except Exception as e:
        print(f"Error reading {f}: {e}")
        continue

    # Parse the old properties from the constructor
    old_props = {}
    for prop in props_to_fix:
        pattern = r'^\s*(' + prop + r':\s*data\?\.[a-zA-Z0-9_]+\s*\|\|\s*[^,\n]+),?'
        match = re.search(pattern, old_content, re.MULTILINE)
        if match:
            old_props[prop] = match.group(1)

    if not old_props:
        continue

    with open(filepath, 'r') as file:
        current_content = file.read()
        
    changed = False
    for prop, old_line in old_props.items():
        curr_pattern = r'^\s*(' + prop + r':\s*data\?\.[a-zA-Z0-9_]+\s*\|\|\s*[^,\n]+),?'
        match = re.search(curr_pattern, current_content, re.MULTILINE)
        if match:
            curr_line = match.group(1)
            if curr_line != old_line:
                print(f"Fixing {f}: {curr_line} -> {old_line}")
                current_content = current_content.replace(curr_line, old_line)
                changed = True

    if changed:
        with open(filepath, 'w') as file:
            file.write(current_content)

print("Done fixing defaults from git history.")
