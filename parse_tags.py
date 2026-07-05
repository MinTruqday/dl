import re

with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    code = f.read()

# very primitive JSX tag counter
tags = re.findall(r'</?([a-zA-Z0-9_]+)[^>]*>', code)

stack = []
for tag in tags:
    tag = tag.split()[0]
    if tag.endswith('/'):
        continue # self closing
    if tag.startswith('/'):
        name = tag[1:]
        if stack and stack[-1] == name:
            stack.pop()
        else:
            print(f"Mismatched closing tag: {tag}, expected {stack[-1] if stack else 'None'}")
    else:
        # ignore self closing like <input ... /> or <div />
        # we can't easily distinguish them here if they have spaces before / like <div />
        pass
