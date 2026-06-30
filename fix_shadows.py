import os
import glob

def fix_shadows():
    target_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/app/(main)"
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith(".tsx"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # We specifically remove 'shadow-sm' from bg-[#F5F5F7] and bg-white rounded cards
                # But keep it on modals (shadow-2xl) or specific toggles if we want,
                # actually let's just remove ' shadow-sm' from cong-tac, bo-suu-tap, etc.
                if "shadow-sm" in content:
                    content = content.replace(" shadow-sm", "")
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

fix_shadows()
