import re

def fix_file(fpath):
    with open(fpath, "r") as f:
        content = f.read()
    
    content = content.replace(".execute())\n        )", ".execute()\n        )")

    with open(fpath, "w") as f:
        f.write(content)

fix_file("backend/management/src/services/account.py")
fix_file("backend/content/src/services/pin.py")
