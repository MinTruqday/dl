import os
import re
import glob

# The directories we want to clean
TARGETS = {
    'services': '_service',
    'router': '_router',
    'schemas': '_schema',
    'models': '_model'
}

# 1. Find all files to rename
renames = {}  # old_path -> new_path
import_replacements = {} # old_import -> new_import

for root, dirs, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root or 'core' in root:
        continue
    parts = root.split(os.sep)
    if len(parts) >= 3 and parts[-1] in TARGETS:
        folder_type = parts[-1]
        suffix = TARGETS[folder_type]
        for f in files:
            if f.endswith(suffix + '.py'):
                base = f[:-len(suffix + '.py')]
                old_path = os.path.join(root, f)
                new_path = os.path.join(root, base + '.py')
                
                # Check for conflicts (e.g. if base.py already exists)
                if not os.path.exists(new_path):
                    renames[old_path] = new_path
                
                # Construct import replacement
                # Example: src.services.user -> src.services.user
                # Need to handle relative imports too if they exist
                old_module = f"src.{folder_type}.{base}{suffix}"
                new_module = f"src.{folder_type}.{base}"
                import_replacements[old_module] = new_module
                
                # Also handle from .user import
                import_replacements[f"from .{base}{suffix}"] = f"from .{base}"
                # Also handle import src.services.user
                import_replacements[f"import src.{folder_type}.{base}{suffix}"] = f"import src.{folder_type}.{base}"

print(f"Found {len(renames)} files to rename.")

# 2. Perform the replacements in ALL python files
for root, _, files in os.walk('.'):
    if 'venv' in root or 'node_modules' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            new_content = content
            for old_imp, new_imp in import_replacements.items():
                # Replace exact matches
                new_content = new_content.replace(old_imp, new_imp)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(new_content)

# 3. Actually rename the files
for old_path, new_path in renames.items():
    os.rename(old_path, new_path)
    print(f"Renamed: {old_path} -> {new_path}")

print("Refactoring complete.")
