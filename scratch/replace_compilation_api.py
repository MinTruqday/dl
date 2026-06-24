import os
import re

def replace_in_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Imports
    content = content.replace(
        'from src.repositories.compilation_document import CompilationDocumentRepository',
        'from src.core.infrastructure.content_client import ContentServiceClient'
    )
    
    # 1. find_one
    content = re.sub(
        r'await CompilationDocumentRepository\.find_one\(\s*\{"_id": ([^,}]+)\}\s*\)',
        r'await ContentServiceClient.get_document(\1)',
        content
    )
    content = re.sub(
        r'await CompilationDocumentRepository\.find_one\(\s*\{"_id": ([^,]+),\s*"creator_id": ([^}]+)\}\s*\)',
        r'await ContentServiceClient.get_document(\1)',
        content
    )
    
    # 2. find_version
    content = re.sub(
        r'await CompilationDocumentRepository\.find_version\(\s*\{"_id": ([^,}]+)\}\s*\)',
        r'await ContentServiceClient.get_document_version(\1)',
        content
    )
    
    # 3. insert_version
    # In insert_version, there is a datetime object which is not serializable if passed directly to httpx JSON.
    # Let's replace the dict literal with one using isoformat.
    content = content.replace('datetime.now(timezone.utc)', 'datetime.now(timezone.utc).isoformat()')

    content = re.sub(
        r'await CompilationDocumentRepository\.insert_version\((.*?)\)',
        r'await ContentServiceClient.create_document_version(\1)',
        content,
        flags=re.DOTALL
    )

    # 4. update_one
    # "await CompilationDocumentRepository.update_one("
    # Since it's multiline, let's use a simpler string replacement for the specific calls
    
    content = content.replace(
        '''await CompilationDocumentRepository.update_one(
            {
                "_id": document_id,
                "$or": [{"creator_id": user_id}, {"co_authors": user_id}],
            },
            {
                "$set": {
                    "draft_content": content,
                    "toc": toc,
                    "reading_time_minutes": reading_time_minutes,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )''',
        '''await ContentServiceClient.update_document(
            document_id,
            {
                "query": {"$or": [{"creator_id": user_id}, {"co_authors": user_id}]},
                "update": {
                    "$set": {
                        "draft_content": content,
                        "toc": toc,
                        "reading_time_minutes": reading_time_minutes,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
            }
        )'''
    )
    
    content = content.replace(
        '''await CompilationDocumentRepository.update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"editor_review_status": "pending_review"}},
        )''',
        '''await ContentServiceClient.update_document(
            document_id,
            {
                "query": {"creator_id": user_id},
                "update": {"$set": {"editor_review_status": "pending_review"}}
            }
        )'''
    )
    
    content = content.replace(
        '''await CompilationDocumentRepository.update_one(
            {"_id": str(document_id)}, {"$set": update_data}
        )''',
        '''await ContentServiceClient.update_document(
            str(document_id),
            {
                "update": {"$set": update_data}
            }
        )'''
    )

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

replace_in_file('./backend/compilation/src/services/composition.py')
print("Replaced API calls")
