import os
import glob

def fix_dependency():
    files = glob.glob('backend/**/src/**/*.py', recursive=True)
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace 'dependency=[Depends(' with 'dependencies=[Depends('
        # Also handle cases like 'dependency=['
        new_content = content.replace('dependency=[Depends', 'dependencies=[Depends')
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")

if __name__ == '__main__':
    fix_dependency()
