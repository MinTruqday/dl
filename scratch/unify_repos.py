import os
import re

backend_dir = './backend'
services = ['content', 'message', 'agentic_ai', 'management', 'compilation']

def get_entity_name(collection_name, base_group):
    # e.g. collection: collaboration_tasks, base_group: collaboration
    # -> task
    if collection_name.startswith(base_group + '_'):
        entity = collection_name[len(base_group)+1:]
    else:
        entity = collection_name
        
    # proper singularize
    if entity == 'status': return 'status'
    if entity == 'activities': return 'activity'
    if entity.endswith('ies'): return entity[:-3] + 'y'
    if entity.endswith('s') and not entity.endswith('ss'): return entity[:-1]
    return entity

for svc in services:
    svc_dir = os.path.join(backend_dir, svc)
    repos_dir = os.path.join(svc_dir, 'src', 'repositories')
    
    if not os.path.exists(repos_dir):
        continue
        
    for repo_file in os.listdir(repos_dir):
        if not repo_file.endswith('.py') or repo_file == '__init__.py':
            continue
            
        group_name = repo_file[:-3]
        repo_class_name = ''.join(x.title() for x in group_name.split('_')) + 'Repository'
        
        file_path = os.path.join(repos_dir, repo_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all old classes and their collections
        # class CollaborationTaskRepository:
        #    ... _get_db()['collaboration_tasks'] ...
        class_pattern = re.compile(r'class ([A-Za-z]+Repository):(.*?)(?=\nclass |\Z)', re.DOTALL)
        method_pattern = re.compile(r'async def ([a-z_]+)\(cls, \*args, \*\*kwargs\):\n\s+return await cls\._get_db\(\)\[\'([a-z_]+)\'\]\.([a-z_]+)\(\*args, \*\*kwargs\)')
        
        old_classes = class_pattern.findall(content)
        if not old_classes: continue
        
        # We will map: OldClass -> { old_method: (new_method, collection) }
        class_mapping = {}
        all_new_methods = []
        
        for old_class, body in old_classes:
            class_mapping[old_class] = {}
            methods = method_pattern.findall(body)
            for m_name, coll_name, db_method in methods:
                entity = get_entity_name(coll_name, group_name)
                
                # e.g. insert_one -> insert_task
                # find_one -> find_task
                action = m_name.split('_')[0] # insert, find, update, delete, count
                
                if entity == group_name or not entity:
                    new_method = m_name # keep as is, e.g. insert_one if it's the root entity
                else:
                    new_method = f"{action}_{entity}"
                    if m_name.endswith('_many') or m_name == 'count_documents':
                        if entity == 'activity': new_method = f"{action}_activities"
                        elif entity == 'status': new_method = f"{action}_status"
                        else: new_method = f"{action}_{entity}s"
                        
                    if m_name == 'count_documents':
                        new_method = f"count_{entity}s"
                
                class_mapping[old_class][m_name] = new_method
                
                method_code = f"""    @classmethod
    async def {new_method}(cls, *args, **kwargs):
        return await cls._get_db()['{coll_name}'].{db_method}(*args, **kwargs)
"""
                if method_code not in all_new_methods:
                    all_new_methods.append(method_code)
                    
        # Rewrite the repository file
        new_repo_content = f"""from typing import Optional, Dict, Any, List
from src.core.infrastructure.database import database
from src.core.infrastructure.configuration import settings

class {repo_class_name}:
    @staticmethod
    def _get_db():
        db_name = settings.SERVICE_DB_NAME if hasattr(settings, 'SERVICE_DB_NAME') else 'doclib'
        return database.mongodb.get_database(db_name)

""" + "\n".join(all_new_methods)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_repo_content)
            
        # Now replace usages in src/services and src/api
        src_dir = os.path.join(svc_dir, 'src')
        for root, _, py_files in os.walk(src_dir):
            for py_file in py_files:
                if not py_file.endswith('.py'): continue
                fpath = os.path.join(root, py_file)
                with open(fpath, 'r', encoding='utf-8') as f:
                    f_content = f.read()
                    
                new_f_content = f_content
                changed = False
                
                for old_class, methods in class_mapping.items():
                    for old_m, new_m in methods.items():
                        old_call = f"{old_class}.{old_m}("
                        new_call = f"{repo_class_name}.{new_m}("
                        if old_call in new_f_content:
                            new_f_content = new_f_content.replace(old_call, new_call)
                            changed = True
                            
                if changed:
                    # Fix imports
                    for old_class in class_mapping.keys():
                        old_import = f"from src.repositories.{group_name} import {old_class}"
                        new_import = f"from src.repositories.{group_name} import {repo_class_name}"
                        if old_import in new_f_content:
                            new_f_content = new_f_content.replace(old_import, new_import)
                        else:
                            # Sometimes it might be imported as a list of classes
                            # We can just replace the old class name with the new one
                            new_f_content = new_f_content.replace(old_class, repo_class_name)
                    
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_f_content)

print("Unified repositories and renamed methods successfully.")
