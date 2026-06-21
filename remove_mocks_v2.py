import os
import re

d = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/features/editor/components'
files = [f for f in os.listdir(d) if f.startswith('DocLib')]

for f in files:
    filepath = os.path.join(d, f)
    with open(filepath, 'r') as file:
        content = file.read()

    # Replace specific default properties with ""
    # opacity: data?.opacity || "0.2" -> opacity: data?.opacity || ""
    content = re.sub(r'(opacity:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(scale:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(format:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(color:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(styleId:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(style:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(width:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(type:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(borderWidth:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(borderStyle:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(borderColor:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(bgColor:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(macroId:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(shape:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(fill:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(stroke:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(float:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(position:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)
    content = re.sub(r'(label:\s*data\?\.[a-zA-Z]+\s*\|\|\s*)"[^"]+"', r'\1""', content)

    with open(filepath, 'w') as file:
        file.write(content)

print("Done removing defaults.")
