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

# Notification Service
noti_user_repo = './backend/notification/src/repositories/user.py'
if os.path.exists(noti_user_repo):
    os.remove(noti_user_repo)

noti_repo = './backend/notification/src/repositories/notification.py'
if os.path.exists(noti_repo):
    with open(noti_repo, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    if 'update_user_announcement_status' not in repo_content:
        repo_content += "\n    @classmethod\n    async def update_user_announcement_status(cls, *args, **kwargs):\n        return await cls._get_db()['users'].update_one(*args, **kwargs)\n"
        with open(noti_repo, 'w', encoding='utf-8') as f:
            f.write(repo_content)

announcement_api = './backend/notification/src/api/announcement.py'
if os.path.exists(announcement_api):
    replace_in_file(announcement_api, {
        'from src.repositories.user import UserRepository': 'from src.repositories.notification import NotificationRepository',
        'UserRepository.update_one': 'NotificationRepository.update_user_announcement_status'
    })

# Collection Service
coll_doc_repo = './backend/collection/src/repositories/document.py'
if os.path.exists(coll_doc_repo):
    os.remove(coll_doc_repo)

coll_archive_repo = './backend/collection/src/repositories/archive.py'
if os.path.exists(coll_archive_repo):
    with open(coll_archive_repo, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    if 'count_documents' not in repo_content:
        repo_content += "\n    @classmethod\n    async def count_documents(cls, *args, **kwargs):\n        return await cls._get_db()['documents'].count_documents(*args, **kwargs)\n"
        with open(coll_archive_repo, 'w', encoding='utf-8') as f:
            f.write(repo_content)

ingest_svc = './backend/collection/src/services/ingestion.py'
if os.path.exists(ingest_svc):
    replace_in_file(ingest_svc, {
        'from src.repositories.document import DocumentRepository\n': '',
        'DocumentRepository.count_documents': 'ArchiveRepository.count_documents'
    })

# Compilation Service
comp_doc_repo = './backend/compilation/src/repositories/document.py'
comp_cdoc_repo = './backend/compilation/src/repositories/compilation_document.py'
if os.path.exists(comp_doc_repo):
    os.rename(comp_doc_repo, comp_cdoc_repo)
    replace_in_file(comp_cdoc_repo, {'DocumentRepository': 'CompilationDocumentRepository'})

comp_dir = './backend/compilation/src'
for root, _, files in os.walk(comp_dir):
    for py_file in files:
        if py_file.endswith('.py'):
            fpath = os.path.join(root, py_file)
            replace_in_file(fpath, {
                'from src.repositories.document import DocumentRepository': 'from src.repositories.compilation_document import CompilationDocumentRepository',
                'DocumentRepository': 'CompilationDocumentRepository'
            })

print("Notification, Collection, Compilation done.")
