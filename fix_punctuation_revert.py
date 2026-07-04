import re
import os

files = [
    'frontend/features/content/components/EditorPage.tsx',
    'frontend/features/compilation/components/Editor.tsx',
    'frontend/features/compilation/components/StandardEditor.tsx',
    'backend/drm/src/api/license.py'
]

for filepath in files:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r') as f:
        content = f.read()

    # Revert "..." to ""
    content = content.replace('...', '')
    
    # We added periods in showToast and setStatusMsg and HTTPException and logger
    # Let's fix them manually for each file because just removing '.' could break something.
    
    if 'EditorPage.tsx' in filepath:
        content = content.replace('Lỗi không xác định."', 'Lỗi không xác định"')
        content = content.replace('Lỗi tải danh sách tài liệu."', 'Lỗi tải danh sách tài liệu"')
        content = content.replace('Đã tải xong."', 'Đã tải xong"')
        content = content.replace('Lỗi tải bản nháp."', 'Lỗi tải bản nháp"')
        content = content.replace('Đang lưu bản nháp"', 'Đang lưu bản nháp"') # Wait we replaced '...' so it's 'Đang lưu bản nháp'
        content = content.replace('Đã lưu bản nháp."', 'Đã lưu bản nháp"')
        content = content.replace('Sẵn sàng."', 'Sẵn sàng"')
        content = content.replace('Lỗi lưu bản thảo."', 'Lỗi lưu bản thảo"')
        content = content.replace('Đang lưu"', 'Đang lưu"')
        content = content.replace('Đã lưu bản nháp thành công."', 'Đã lưu bản nháp thành công"')
        content = content.replace('Không thể lưu bản nháp."', 'Không thể lưu bản nháp"')
        content = content.replace('Đang xuất bản"', 'Đang xuất bản"')
        content = content.replace('Tài liệu đã được công bố."', 'Tài liệu đã được công bố"')
        content = content.replace('Xuất bản thất bại."', 'Xuất bản thất bại"')
        content = content.replace('Đang tạo PDF"', 'Đang tạo PDF"')
        content = content.replace('Tải PDF thành công."', 'Tải PDF thành công"')
        content = content.replace('Lỗi tạo PDF."', 'Lỗi tạo PDF"')
        content = content.replace('Đang tạo DOCX"', 'Đang tạo DOCX"')
        content = content.replace('Tải DOCX thành công."', 'Tải DOCX thành công"')
        content = content.replace('Lỗi tạo DOCX."', 'Lỗi tạo DOCX"')

    if 'Editor.tsx' in filepath:
        content = content.replace('gói Cao cấp."', 'gói Cao cấp"')
        content = content.replace('kiểm tra ngữ pháp."', 'kiểm tra ngữ pháp"')
        content = content.replace('ngữ pháp bằng AI"', 'ngữ pháp bằng AI"')
        content = content.replace('máy chủ AI."', 'máy chủ AI"')
        content = content.replace('mã nguồn LaTeX"', 'mã nguồn LaTeX"')
        content = content.replace('dung để biên dịch."', 'dung để biên dịch"')
        content = content.replace('biên dịch LaTeX."', 'biên dịch LaTeX"')
        content = content.replace('sang Word"', 'sang Word"')
        content = content.replace('Word thành công."', 'Word thành công"')
        content = content.replace('xuất Word."', 'xuất Word"')
        content = content.replace('cập nhật."', 'cập nhật"')
        content = content.replace('thay thế nội dung."', 'thay thế nội dung"')
        content = content.replace('nghĩa.",', 'nghĩa",')
        content = content.replace('})}.", "info"', '})}", "info"')
        content = content.replace('phù hợp."', 'phù hợp"')
        content = content.replace('lúc này."', 'lúc này"')
        content = content.replace('thanh bên."', 'thanh bên"')
        content = content.replace('}].", "error"', '}]`, "error"')
        content = content.replace('chương trước."', 'chương trước"')
        content = content.replace('nhất quán."', 'nhất quán"')
        content = content.replace('lòng đợi.`', 'lòng đợi`')
        content = content.replace('dịch thành công."', 'dịch thành công"')
        content = content.replace('Lỗi dịch thuật."', 'Lỗi dịch thuật"')
        content = content.replace('nguyên bản."', 'nguyên bản"')

    if 'StandardEditor.tsx' in filepath:
        content = content.replace('Đang lưu"', 'Đang lưu"')
        content = content.replace('Đã lưu."', 'Đã lưu"')
        content = content.replace('Lỗi lưu bản thảo."', 'Lỗi lưu bản thảo"')
        content = content.replace('lưu nội dung."', 'lưu nội dung"')
        
    if 'license.py' in filepath:
        content = content.replace('liệu: {req.file_id}."', 'liệu: {req.file_id}"')
        content = content.replace('tài liệu."', 'tài liệu"')
        content = content.replace('hết hạn."', 'hết hạn"')
        content = content.replace('file này."', 'file này"')
        content = content.replace('tài liệu này."', 'tài liệu này"')
        content = content.replace('hệ thống."', 'hệ thống"')
        content = content.replace('hợp lệ."', 'hợp lệ"')
        content = content.replace('user_id}."', 'user_id}"')
        
    with open(filepath, 'w') as f:
        f.write(content)

