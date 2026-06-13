import os
import re

backend_replacements = {
    'backend/authentication/src/api/authentication_router.py': [
        ('/quen-mat-khau', '/forgot-password'),
        ('/dat-lai-mat-khau', '/reset-password'),
        ('/ma-xac-thuc', '/verify-code')
    ],
    'backend/content/src/api/document_router.py': [
        ('/danh-sach', '/list'),
        ('/ca-nhan', '/personal'),
        ('/chuoi-tai-lieu', '/series'),
        ('/thu-muc', '/folder'),
        ('/thung-rac', '/trash'),
        ('/mo-khoa', '/unlock')
    ],
    'backend/content/src/api/storage_router.py': [
        ('/thu-muc', '/folder'),
        ('/tap-tin', '/file'),
        ('/danh-sach', '/list'),
        ('/tai-xuong-zip', '/download-zip'),
        ('/gan-day', '/recent'),
        ('/tim-kiem', '/search'),
        ('/chia-se', '/share')
    ],
    'backend/content/src/api/upload_router.py': [
        ('/tap-tin', '/file'),
        ('/hinh-anh', '/image'),
        ('/phan-doan', '/chunk')
    ],
    'backend/content/src/api/reading_router.py': [
        ('/muc-tieu', '/goal'),
        ('/tien-do', '/progress'),
        ('/trinh-bay', '/layout'),
        ('/cay-thu-muc-zip', '/tree-zip'),
        ('/noi-dung-zip', '/content-zip')
    ],
    'backend/content/src/api/highlight_router.py': [
        ('/ghi-chu', '/note')
    ],
    'backend/content/src/api/bookmark_router.py': [
        ('/thu-muc', '/folder')
    ],
    'backend/content/src/api/discovery_router.py': [
        ('/xu-huong', '/trending'),
        ('/the-va-danh-muc', '/tags-categories'),
        ('/tim-kiem-thong-minh', '/smart-search'),
        ('/goi-y/ai', '/ai-suggestion'),
        ('/hashtag-xu-huong', '/trending-hashtags'),
        ('/phan-loai', '/classification')
    ],
    'backend/content/src/api/publication_router.py': [
        ('/doc-thu', '/preview'),
        ('/tinh-phi', '/monetize'),
        ('/len-lich', '/schedule'),
        ('/seo', '/seo'),
        ('/doc-hieu', '/reading-comprehension')
    ],
    'backend/content/src/api/version_router.py': [
        ('/luu', '/save'),
        ('/khoi-phuc', '/restore')
    ],
    'backend/content/src/api/collaboration_router.py': [
        ('/loi-moi', '/invite'),
        ('/nhiem-vu', '/task'),
        ('/tham-gia', '/join'),
        ('/khoa', '/lock'),
        ('/mo-khoa', '/unlock'),
        ('/ma-moi', '/invite-code'),
        ('/truc-tuyen', '/online'),
        ('/quyen-truy-cap', '/access'),
        ('/chuyen-quyen', '/transfer-owner')
    ],
    'backend/finance/src/api/wallet_router.py': [
        ('/so-du', '/balance'),
        ('/lich-su', '/history'),
        ('/doanh-thu', '/revenue'),
        ('/mua', '/purchase')
    ],
    'backend/finance/src/api/deposit_router.py': [
        ('/tao-link', '/create-link'),
        ('/kiem-tra', '/check')
    ],
    'backend/provision/src/api/user_router.py': [
        ('/tim-kiem', '/search'),
        ('/tao-moi', '/create')
    ],
    'backend/provision/src/api/telemetry_router.py': [
        ('/kiem-tra', '/check'),
        ('/thong-ke', '/statistics'),
        ('/suc-khoe-he-thong', '/health'),
        ('/hoat-dong', '/activity')
    ],
    'backend/provision/src/api/quota_router.py': [
        ('/kiem-tra', '/check'),
        ('/cau-hinh', '/config')
    ],
    'backend/agentic_ai/src/api/chat_router.py': [
        ('/truy-van', '/rag-query') # just in case
    ],
    'backend/agentic_ai/src/api/ingest_router.py': [
        ('/dong-bo', '/sync')
    ],
    'backend/signal/src/api/notification_router.py': [
        ('/danh-dau-tat-ca', '/read-all')
    ]
}

for file, replaces in backend_replacements.items():
    if not os.path.exists(file):
        continue
    with open(file, 'r') as f:
        content = f.read()
    
    for old, new in replaces:
        content = content.replace(f'("{old}"', f'("{new}"').replace(f'("{old}', f'("{new}')
        
    with open(file, 'w') as f:
        f.write(content)
    print(f"Updated {file}")

