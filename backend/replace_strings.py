import json
import os
import glob

def load_translations():
    translations = {}
    for i in range(1, 9):
        filename = f"vi_{i}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                translations.update(data)
    return translations

def replace_in_files(translations):
    python_files = []
    for root, _, files in os.walk('.'):
        for f in files:
            if f.endswith('.py') and 'venv' not in root and 'node_modules' not in root:
                python_files.append(os.path.join(root, f))
    
    total_replaced = 0
    for path in python_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for eng, vi in translations.items():
                # Normal string replacements
                content = content.replace(f'"{eng}"', f'"{vi}"')
                content = content.replace(f"'{eng}'", f"'{vi}'")
                # F-string replacements
                content = content.replace(f'f"{eng}"', f'f"{vi}"')
                content = content.replace(f"f'{eng}'", f"f'{vi}'")
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                total_replaced += 1
                print(f"Updated {path}")
        except Exception as e:
            print(f"Error processing {path}: {e}")
            
    print(f"Total files updated: {total_replaced}")

if __name__ == "__main__":
    translations = load_translations()
    print(f"Loaded {len(translations)} translations.")
    replace_in_files(translations)
