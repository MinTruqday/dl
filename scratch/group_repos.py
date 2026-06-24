import os
import re

backend_dir = './backend'

groupings = {
    'content': {
        'collaboration': [
            'collaboration_activitie', 'collaboration_draft', 'collaboration_invite',
            'collaboration_invite_code', 'collaboration_lock', 'collaboration_memo',
            'collaboration_statu', 'collaboration_task', 'collaboration_task_comment'
        ],
        'document': ['document', 'document_revision', 'document_version'],
        'reading': ['reading_history', 'reading_list'],
        'bookmark': ['bookmark_folder'],
        'copyright': ['copyright_dispute'],
        'user': ['user_content_profile']
    },
    'message': {
        'message': ['message', 'message_group', 'message_setting'],
        'user': ['user_contact_profile']
    },
    'agentic_ai': {
        'finetune': ['finetune_job', 'finetune_dataset', 'finetune_sample'],
        'chat': ['ai_message', 'ai_session'],
        'agent': ['agent_trace']
    },
    'management': {
        'system': ['system_config', 'telemetry', 'audit_log'],
        'moderation': ['moderator_note', 'warning', 'report', 'bug_report']
    },
    'compilation': {
        'editor': ['editor_suggestion', 'editor_comment'],
        'document': ['document', 'document_version'],
        'pomodoro': ['pomodoro_session']
    }
}

for svc, groups in groupings.items():
    svc_dir = os.path.join(backend_dir, svc)
    repos_dir = os.path.join(svc_dir, 'src', 'repositories')
    
    if not os.path.exists(repos_dir):
        continue

    for group_name, files in groups.items():
        group_file = os.path.join(repos_dir, f"{group_name}.py")
        
        # We will collect classes from all files in `files`
        combined_content = ""
        classes_to_move = []
        
        for f in files:
            f_path = os.path.join(repos_dir, f"{f}.py")
            if os.path.exists(f_path):
                with open(f_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # Extract class definitions. We can just strip the imports from the top.
                    lines = content.split('\n')
                    class_start = 0
                    for i, line in enumerate(lines):
                        if line.startswith('class '):
                            class_start = i
                            class_name = line.split(' ')[1].split(':')[0]
                            classes_to_move.append((f, class_name))
                            break
                    
                    if class_start > 0:
                        combined_content += "\n" + "\n".join(lines[class_start:]) + "\n"
                
                os.remove(f_path)
        
        if combined_content:
            # Check if group file already exists to preserve imports, else create
            if os.path.exists(group_file):
                with open(group_file, 'a', encoding='utf-8') as file:
                    file.write(combined_content)
            else:
                header = (
                    "from typing import Optional, Dict, Any, List\n"
                    "from src.core.infrastructure.database import database\n"
                    "from src.core.infrastructure.configuration import settings\n"
                )
                with open(group_file, 'w', encoding='utf-8') as file:
                    file.write(header + combined_content)
        
        # Now update all imports in src/
        src_dir = os.path.join(svc_dir, 'src')
        for root, _, py_files in os.walk(src_dir):
            for py_file in py_files:
                if py_file.endswith('.py'):
                    fpath = os.path.join(root, py_file)
                    with open(fpath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    new_content = content
                    for old_file, class_name in classes_to_move:
                        if old_file != group_name:
                            old_import = f"from src.repositories.{old_file} import {class_name}"
                            new_import = f"from src.repositories.{group_name} import {class_name}"
                            new_content = new_content.replace(old_import, new_import)
                    
                    if new_content != content:
                        with open(fpath, 'w', encoding='utf-8') as file:
                            file.write(new_content)

print("Grouped repositories successfully.")
