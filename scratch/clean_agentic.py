import os
import re

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

# 1. agentic_ai
agentic_ai_svc = './backend/agentic_ai/src/services/finetuning.py'
if os.path.exists(agentic_ai_svc):
    replace_in_file(agentic_ai_svc, {
        'from src.repositories.document import DocumentRepository\n': '',
        'DocumentRepository.find_one': 'FinetuneRepository.find_document_context'
    })
    
    finetune_repo = './backend/agentic_ai/src/repositories/finetune.py'
    if os.path.exists(finetune_repo):
        with open(finetune_repo, 'r', encoding='utf-8') as f:
            repo_content = f.read()
        if 'find_document_context' not in repo_content:
            repo_content += "\n    @classmethod\n    async def find_document_context(cls, *args, **kwargs):\n        return await cls._get_db()['documents'].find_one(*args, **kwargs)\n"
            with open(finetune_repo, 'w', encoding='utf-8') as f:
                f.write(repo_content)
    
    doc_repo = './backend/agentic_ai/src/repositories/document.py'
    if os.path.exists(doc_repo):
        os.remove(doc_repo)

print("Agentic AI done.")
