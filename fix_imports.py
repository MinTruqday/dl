import os
import re

for root, _, files in os.walk('backend'):
    if 'venv' in root or 'node_modules' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            original_content = content
            
            # Replace import of inference
            if 'agentic_ai' in path:
                content = content.replace("from core.schemas.inference import", "from src.schemas.inference import")
            elif 'editor' in path:
                # Editor might not have inference schema anymore? Wait, editor used inference.py
                # Let's see... editor used core.schemas.inference. We should copy inference to editor/src/schemas
                pass
            
            # Replace imports of user schemas
            # If it's in management, it uses src.schemas.user
            if 'management' in path:
                content = content.replace("from core.schemas.user import", "from src.schemas.user import")
                content = content.replace("from core.schemas.quota import", "from src.schemas.quota import")
                content = content.replace("from core.schemas.collector import", "from src.schemas.collector import")
                # Wait, management also needs CurrentUser from core.dependency for endpoints
                # Actually, in management, UserInDB from src.schemas.user is fine for typing.
                # But get_current_user returns CurrentUser now!
                # It's okay, python duck typing will allow it, or we replace UserInDB with CurrentUser for Depends(get_current_user)
                content = content.replace("current_user: UserInDB = Depends", "current_user: CurrentUser = Depends")
                # add import if needed
                if "CurrentUser = Depends" in content and "CurrentUser" not in content[:content.find("CurrentUser = Depends")]:
                    content = "from core.dependency import CurrentUser\n" + content
            elif 'authentication' in path:
                content = content.replace("from core.schemas.user import", "from src.schemas.user import")
                content = content.replace("current_user: UserInDB = Depends", "current_user: CurrentUser = Depends")
                if "CurrentUser = Depends" in content and "CurrentUser" not in content[:content.find("CurrentUser = Depends")]:
                    content = "from core.dependency import CurrentUser\n" + content
            else:
                # Other services just need CurrentUser and RoleEnum
                # Replace 'from core.schemas.user import ... UserInDB ...' with 'from core.dependency import CurrentUser, RoleEnum'
                # Let's just do text replacements
                content = re.sub(r'from core\.schemas\.user import[^\n]*\n', 'from core.dependency import CurrentUser, RoleEnum\n', content)
                content = content.replace("UserInDB", "CurrentUser")
                
                # Replace quota, inference, collector if they are in other services
                content = content.replace("from core.schemas.collector import", "from src.schemas.collector import")
                content = content.replace("from core.schemas.inference import", "from src.schemas.inference import")
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Fixed imports in {path}")

