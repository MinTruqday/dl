import os
import re
import glob

MAPPING = {
    "CollaborationActivitieRepository": "collaboration_activities",
    "CollaborationTaskCommentRepository": "collaboration_task_comments",
    "CollaborationTaskRepository": "collaboration_tasks",
    "CollaborationInviteRepository": "collaboration_invites",
    "CollaborationDraftRepository": "collaboration_drafts",
    "CollaborationMemoRepository": "collaboration_memos",
    "DocumentVersionRepository": "document_versions",
    "ReadingHistoryRepository": "reading_history",
    "ReadingListRepository": "reading_lists",
    "BookmarkFolderRepository": "bookmark_folders",
    "AuditLogRepository": "audit_logs",
}

def fix_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    changed = False
    for repo, collection in MAPPING.items():
        # Replace `await Repo \n .find(...)` or `await Repo.find(...)`
        # We can use regex to match `Repo[\s\n]*\.[\s\n]*find\(`
        pattern = r'\b' + repo + r'\b([\s\n]*)\.([\s\n]*)find\('
        
        def repl(match):
            return f'mongo{match.group(1)}.{match.group(2)}find("{collection}", '
        
        new_content, count = re.subn(pattern, repl, content)
        if count > 0:
            content = new_content
            changed = True
            print(f"Replaced {repo} -> {collection} in {filepath}")
            
        # Also handle `.aggregate(`
        pattern_agg = r'\b' + repo + r'\b([\s\n]*)\.([\s\n]*)aggregate\('
        def repl_agg(match):
            return f'mongo{match.group(1)}.{match.group(2)}aggregate("{collection}", '
        
        new_content, count = re.subn(pattern_agg, repl_agg, content)
        if count > 0:
            content = new_content
            changed = True
            print(f"Replaced {repo} -> {collection} (aggregate) in {filepath}")

    if changed:
        # ensure `mongo` is imported if not already
        if "from src.core.infrastructure.mongo import mongo" not in content:
            content = "from src.core.infrastructure.mongo import mongo\n" + content
        with open(filepath, "w") as f:
            f.write(content)

if __name__ == "__main__":
    for filepath in glob.glob("backend/content/src/services/*.py"):
        fix_file(filepath)
