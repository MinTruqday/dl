import os
import glob
import re

replacements = {
    'backend/provision/src/api/telemetry_router.py': ('/do-luong', '/telemetry'),
    'backend/provision/src/api/operation_router.py': ('/van-hanh', '/operation'),
    'backend/content/src/api/publication_router.py': ('/export-ban', '/publication'),
    'backend/content/src/api/draft_router.py': ('/ban-nhap', '/draft'),
    'backend/content/src/api/export_router.py': ('/export-tai-lieu', '/export'),
    'backend/content/src/api/bookmark_router.py': ('/dau-trang', '/bookmark'),
    'backend/content/src/api/review_router.py': ('/evaluate', '/review'),
    'backend/content/src/api/highlight_router.py': ('/neu-bat', '/highlight'),
    'backend/content/src/api/reading_router.py': ('/doc', '/reading'),
    'backend/content/src/api/pin_router.py': ('/ghim', '/pin'),
}

for filepath, (old_prefix, new_prefix) in replacements.items():
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        content = content.replace(f'prefix="{old_prefix}"', f'prefix="{new_prefix}"')
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed prefix in {filepath}")

# Now fix docker-compose.yml Traefik rules
with open('docker-compose.yml', 'r') as f:
    content = f.read()

content = content.replace('PathPrefix(`/danh-dau`)', 'PathPrefix(`/bookmark`)')
content = content.replace('PathPrefix(`/han-muc`)', 'PathPrefix(`/quota`)')

# Add /quota to provision
content = content.replace(
    'PathPrefix(`/user`) || PathPrefix(`/audit`) || PathPrefix(`/telemetry`) || PathPrefix(`/operation`)',
    'PathPrefix(`/user`) || PathPrefix(`/audit`) || PathPrefix(`/telemetry`) || PathPrefix(`/operation`) || PathPrefix(`/quota`)'
)

with open('docker-compose.yml', 'w') as f:
    f.write(content)
print("Fixed docker-compose.yml")
