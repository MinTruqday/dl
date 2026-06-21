import os
import re

d = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/features/editor/components'
files = [f for f in os.listdir(d) if f.startswith('DocLib')]

replacements = [
    # property name, restored default value
    ('opacity', '"0.2"'),
    ('scale', '"100%"'),
    ('format', '"locale"'),
    ('color', '"#ffffff"'),
    ('styleId', '"style1"'),
    ('style', '"solid"'),
    ('width', '"100%"'), # Note: DocLibPageBorder used "4px", DocLibTextBox used "100%". We need to handle them carefully.
    ('type', '"continuous"'),
    ('borderWidth', '"2px"'),
    ('borderStyle', '"solid"'),
    ('borderColor', '"#3b82f6"'),
    ('bgColor', '"#eff6ff"'),
    ('macroId', '"macro_1"'),
    ('shape', '"rectangle"'),
    ('fill', '"#3b82f6"'),
    ('stroke', '"#1d4ed8"'),
    ('float', '"none"'),
    ('position', '"bottom-right"'),
    ('label', '"DocLib Button"'),
]

for f in files:
    filepath = os.path.join(d, f)
    with open(filepath, 'r') as file:
        content = file.read()
        
    changed = False

    # Specific file overrides
    if f == 'DocLibPageBorder.ts':
        if re.search(r'width:\s*data\?\.[a-zA-Z]+\s*\|\|\s*\"\"', content):
            content = re.sub(r'(width:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)\"\"', r'\1"4px"', content)
            changed = True
        if re.search(r'color:\s*data\?\.[a-zA-Z]+\s*\|\|\s*\"\"', content):
            content = re.sub(r'(color:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)\"\"', r'\1"#0f172a"', content)
            changed = True
            
    if f == 'DocLibPageNumber.ts':
        if re.search(r'format:\s*data\?\.[a-zA-Z]+\s*\|\|\s*\"\"', content):
            content = re.sub(r'(format:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)\"\"', r'\1"1, 2, 3"', content)
            changed = True

    # Generic replacements
    for prop, default_val in replacements:
        pattern = r'(' + prop + r':\s*data\?\.[a-zA-Z]+\s*\|\|\s*)\"\"'
        if re.search(pattern, content):
            content = re.sub(pattern, r'\g<1>' + default_val, content)
            changed = True

    if changed:
        with open(filepath, 'w') as file:
            file.write(content)

print("Done restoring defaults.")
