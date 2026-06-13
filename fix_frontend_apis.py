import os
import glob
import re

replacements = {
    # AI mappings
    '/ai/van-ban': '/inference/generate-content',
    '/ai/bien-doi-van-ban': '/inference/text-transform',
    '/ai/tham-dinh-noi-dung': '/inference/content-moderation',
    '/ai/tong-hop-da-tai-lieu': '/inference/multi-doc-synthesis',
    '/ai/trich-dan-thong-minh': '/inference/smart-citation',
    '/ai/chat': '/chat/chat',
    '/ai/truy-van': '/chat/rag-query',
    '/ai/luong': '/chat/stream',
    '/ai/dong-bo': '/ingest/sync',
    '/ai/lich-su': '/history',
    '/ai/tai-lieu-luu-tru/': '/inference/document-analysis/', # Just a guess, since inference_router has document-analysis
    
    # Auth mappings
    '/auth/ca-nhan': '/auth/personal',
    '/auth/forgot-password': '/auth/forgot-password',
    '/auth/reset-password': '/auth/reset-password',
    '/auth/quen-mat-khau': '/auth/forgot-password',
    '/auth/ma-xac-thuc': '/auth/verify-code',
    '/auth/dat-lai-mat-khau': '/auth/reset-password',
    '/auth/passkey/login/bat-dau': '/auth/passkey/login/start',
    '/auth/passkey/register/bat-dau': '/auth/passkey/register/start',
    
    # Content mappings
    '/bookmark/thu-muc': '/bookmark/folder',
    '/collaboration/loi-moi': '/collaboration/invite',
    '/collaboration/nhiem-vu': '/collaboration/task',
    '/collaboration/tham-gia': '/collaboration/join',
    '/collaboration/document/': '/collaboration/document/', # keep
    '/khoa': '/lock',
    '/mo-khoa': '/unlock',
    '/ma-moi': '/invite-code',
    '/truc-tuyen': '/online',
    '/quyen-truy-cap': '/access',
    '/chuyen-quyen': '/transfer-owner',
    
    '/document/ca-nhan': '/document/personal',
    '/document/chuoi-tai-lieu': '/document/series',
    '/document/thu-muc': '/document/folder',
    '/document/thung-rac': '/document/trash',
    '/document/d/': '/document/d/', # keep
    
    '/discovery/xu-huong': '/discovery/trending',
    '/discovery/the-va-danh-muc': '/discovery/tags-categories',
    '/discovery/tim-kiem-thong-minh': '/discovery/smart-search',
    '/discovery/goi-y/ai': '/discovery/ai-suggestion',
    '/discovery/hashtag-xu-huong': '/discovery/trending-hashtags',
    '/discovery/phan-loai': '/discovery/classification',
    
    '/publication/doc-thu': '/publication/preview',
    '/publication/tinh-phi': '/publication/monetize',
    '/publication/len-lich': '/publication/schedule',
    '/publication/seo': '/publication/seo',
    '/publication/doc-hieu': '/publication/reading-comprehension',
    
    '/reading/muc-tieu': '/reading/goal',
    '/reading/tien-do': '/reading/progress',
    '/reading/trinh-bay': '/reading/layout',
    '/reading/cay-thu-muc-zip': '/reading/tree-zip',
    '/reading/noi-dung-zip': '/reading/content-zip',
    
    '/highlight/ghi-chu': '/highlight/note',
    '/version/luu': '/version/save',
    '/version/khoi-phuc': '/version/restore',
    
    '/storage/thu-muc': '/storage/folder',
    '/storage/tap-tin': '/storage/file',
    '/storage/danh-sach': '/storage/list',
    '/storage/tai-xuong-zip': '/storage/download-zip',
    '/storage/gan-day': '/storage/recent',
    '/storage/tim-kiem': '/storage/search',
    '/storage/chia-se': '/storage/share',
    
    '/upload/tap-tin': '/upload/file',
    '/upload/hinh-anh': '/upload/image',
    '/upload/phan-doan': '/upload/chunk',
    
    # Provision & Telemetry
    '/user/tim-kiem': '/user/search',
    '/user/tao-moi': '/user/create',
    '/telemetry/kiem-tra': '/telemetry/check',
    '/telemetry/thong-ke': '/telemetry/statistics',
    '/telemetry/suc-khoe-he-thong': '/telemetry/health',
    '/telemetry/hoat-dong': '/telemetry/activity',
    '/quota/kiem-tra': '/quota/check',
    '/quota/cau-hinh': '/quota/config',
    
    # Finance
    '/wallet/so-du': '/wallet/balance',
    '/wallet/lich-su': '/wallet/history',
    '/wallet/doanh-thu': '/wallet/revenue',
    '/deposit/tao-link': '/deposit/create-link',
    '/deposit/kiem-tra': '/deposit/check',
    
    # Signal
    '/notification/danh-dau-tat-ca': '/notification/read-all',
}

def fix_frontend():
    files = glob.glob('frontend/**/*.ts', recursive=True) + glob.glob('frontend/**/*.tsx', recursive=True)
    count = 0
    for file in files:
        with open(file, 'r') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements.items():
            # Apply replacements globally in the file
            new_content = new_content.replace(old, new)
            
        if new_content != content:
            with open(file, 'w') as f:
                f.write(new_content)
            count += 1
            print(f"Fixed {file}")
            
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    fix_frontend()
