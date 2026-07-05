import sys

with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    lines = f.readlines()

braces = 0
for i, line in enumerate(lines):
    for c in line:
        if c == '{': braces += 1
        elif c == '}': braces -= 1
    if braces < 0:
        print(f"Extra closing brace at line {i+1}")
        braces = 0

print("Final braces balance:", braces)
