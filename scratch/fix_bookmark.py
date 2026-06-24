import os

def replace_in_file(fpath, old_str, new_str):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_str in content:
        content = content.replace(old_str, new_str)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

replace_in_file('./backend/content/src/services/bookmark.py', 'UserRepository', 'ContentProfileRepository')
replace_in_file('./backend/content/src/services/bookmark.py', 'src.repositories.user', 'src.repositories.profile')

print("Replaced UserRepository in bookmark.py")
