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

# Message Service
# 1. Rename user.py to profile.py
user_repo = './backend/message/src/repositories/user.py'
profile_repo = './backend/message/src/repositories/profile.py'
if os.path.exists(user_repo):
    os.rename(user_repo, profile_repo)
    replace_in_file(profile_repo, {'UserRepository': 'ContactProfileRepository'})

# 2. Update usages of UserRepository in message service
msg_dir = './backend/message/src'
for root, _, files in os.walk(msg_dir):
    for py_file in files:
        if py_file.endswith('.py'):
            fpath = os.path.join(root, py_file)
            replace_in_file(fpath, {
                'from src.repositories.user import UserRepository': 'from src.repositories.profile import ContactProfileRepository',
                'UserRepository': 'ContactProfileRepository'
            })

# 3. DocumentRepository
msg_doc_repo = './backend/message/src/repositories/document.py'
if os.path.exists(msg_doc_repo):
    os.remove(msg_doc_repo)

message_repo = './backend/message/src/repositories/message.py'
if os.path.exists(message_repo):
    with open(message_repo, 'r', encoding='utf-8') as f:
        repo_content = f.read()
    if 'find_shared_document' not in repo_content:
        repo_content += "\n    @classmethod\n    async def find_shared_document(cls, *args, **kwargs):\n        return await cls._get_db()['documents'].find_one(*args, **kwargs)\n"
        with open(message_repo, 'w', encoding='utf-8') as f:
            f.write(repo_content)

thread_svc = './backend/message/src/services/thread.py'
if os.path.exists(thread_svc):
    replace_in_file(thread_svc, {
        'from src.repositories.document import DocumentRepository\n': '',
        'DocumentRepository.find_one': 'MessageRepository.find_shared_document'
    })

print("Message Service done.")
