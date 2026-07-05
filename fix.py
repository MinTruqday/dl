with open('frontend/app/(main)/luu-tru/page.tsx', 'r') as f:
    lines = f.readlines()

# delete lines 906 through 1106 (index 905 to 1106)
del lines[905:1106]

with open('frontend/app/(main)/luu-tru/page.tsx', 'w') as f:
    f.writelines(lines)
