import os

def replace_in_file(fpath, replacements):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    changed = False
    for old_str, new_str in replacements.items():
        if old_str in content:
            content = content.replace(old_str, new_str)
            changed = True
    if changed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

svc_path = './backend/compilation/src/services/composition.py'
replace_in_file(svc_path, {
    'from src.repositories.editor import EditorRepository': 'from src.repositories.composition import CompositionRepository',
    'EditorRepository': 'CompositionRepository',
    'CompilationCompilationDocumentRepository': 'CompilationDocumentRepository',
    'EditorCommentRepository': 'CompositionRepository'
})

print("Fixed composition.py service")
