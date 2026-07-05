import re

with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    code = f.read()

# Very basic check for unmatched braces
braces = 0
for i, c in enumerate(code):
    if c == '{': braces += 1
    elif c == '}': braces -= 1
    
print("Unmatched braces:", braces)
