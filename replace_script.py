import os
import glob

def replace_in_files(glob_pattern, old_str, new_str):
    for filepath in glob.glob(glob_pattern, recursive=True):
        if not os.path.isfile(filepath):
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_str in content:
            new_content = content.replace(old_str, new_str)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Replaced in {filepath}")

if __name__ == "__main__":
    base_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib"
    
    # Task 1
    replace_in_files(
        f"{base_dir}/backend/content/src/router/**/*.py",
        "from src.dependencies import ",
        "from core.dependency import "
    )
    
    # Task 2
    replace_in_files(
        f"{base_dir}/backend/agentic_ai/src/**/*.py",
        "from src.core.prompt_registry import PromptType, prompt_registry",
        "from src.core.prompts import PromptType, prompt_registry"
    )
