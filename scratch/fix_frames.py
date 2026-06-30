import os
import re
import glob

pages = glob.glob("frontend/app/(main)/*/page.tsx") + glob.glob("frontend/app/(main)/*/*/page.tsx")

for path in pages:
    with open(path, "r") as f:
        content = f.read()

    original = content
    
    # 1. Remove outer grey frame for tables and grids
    # Variation 1
    content = content.replace(
        'className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] flex-1 overflow-y-auto no-scrollbar"',
        'className="flex-1 overflow-y-auto no-scrollbar"'
    )
    # Variation 2
    content = content.replace(
        'className="bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] overflow-hidden flex flex-col flex-1 min-h-0"',
        'className="flex flex-col flex-1 min-h-0"'
    )
    # Variation 3 (sometimes no border class)
    content = content.replace(
        'className="bg-[#F5F5F7] rounded-[24px] flex-1 overflow-y-auto no-scrollbar"',
        'className="flex-1 overflow-y-auto no-scrollbar"'
    )
    
    # 2. Fix table row borders to be visible on white bg
    content = content.replace('border-[#F5F5F7] hover:bg-[#F5F5F7]', 'border-[#E8E8ED] hover:bg-[#F5F5F7]')
    
    # 3. Standardize the grid/list buttons
    # We use regex to match the various grid/list toggle HTML
    regex = r'<div className="flex bg-\[#(?:F5F5F7|E8E8ED)\] rounded-\[12px\] p-0\.5.*?LayoutGrid.*?List.*?</div>'
    
    standard_btn = """<div className="flex bg-[#E8E8ED] rounded-full p-0.5 shrink-0">
            <button onClick={() => setViewMode("list")} className={`p-1 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><List className="w-4 h-4" /></button>
            <button onClick={() => setViewMode("grid")} className={`p-1 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><LayoutGrid className="w-4 h-4" /></button>
          </div>"""
          
    content = re.sub(regex, standard_btn, content, flags=re.DOTALL)
    
    # Check if there's any other toggle variations
    regex2 = r'<div className="flex bg-\[#(?:F5F5F7|E8E8ED)\] p-1 rounded-full shrink-0">.*?LayoutGrid.*?List.*?</div>'
    content = re.sub(regex2, standard_btn, content, flags=re.DOTALL)
    
    if content != original:
        with open(path, "w") as f:
            f.write(content)
        print(f"Updated {path}")

