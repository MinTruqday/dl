import os
import glob

pages = glob.glob("frontend/app/(main)/*/page.tsx")

for path in pages:
    with open(path, "r") as f:
        content = f.read()

    original = content
    
    # bao-cao
    content = content.replace(
        'className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex-1 overflow-hidden flex flex-col min-h-0"',
        'className="flex-1 overflow-hidden flex flex-col min-h-0"'
    )
    # tinh-chinh
    content = content.replace(
        'className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex flex-col overflow-hidden min-h-0"',
        'className="flex flex-col overflow-hidden min-h-0"'
    )
    
    if content != original:
        with open(path, "w") as f:
            f.write(content)
        print(f"Updated {path}")

