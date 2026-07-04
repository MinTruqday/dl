import re

with open('frontend/features/compilation/components/Editor.tsx', 'r') as f:
    content = f.read()

replacements = {
    '"Tính năng AI này chỉ dành cho gói Cao cấp"': '"Tính năng AI này chỉ dành cho gói Cao cấp."',
    '"Vui lòng viết thêm nội dung để kiểm tra ngữ pháp"': '"Vui lòng viết thêm nội dung để kiểm tra ngữ pháp."',
    '"Đang phân tích ngữ pháp bằng AI"': '"Đang phân tích ngữ pháp bằng AI..."',
    'err.message || "Lỗi kết nối máy chủ AI"': 'err.message || "Lỗi kết nối máy chủ AI."',
    '"Đang biên dịch mã nguồn LaTeX"': '"Đang biên dịch mã nguồn LaTeX..."',
    '"Vui lòng nhập nội dung để biên dịch"': '"Vui lòng nhập nội dung để biên dịch."',
    '"Biên dịch LaTeX thành công"': '"Biên dịch LaTeX thành công."',
    'err.message || "Lỗi khi biên dịch LaTeX"': 'err.message || "Không thể biên dịch LaTeX."',
    '"Đang xuất tài liệu sang Word"': '"Đang xuất tài liệu sang Word..."',
    '"Xuất Word thành công"': '"Xuất Word thành công."',
    'err.message || "Lỗi khi xuất Word"': 'err.message || "Không thể xuất Word."',
    '"Đã thay thế thành công, nội dung sẽ được cập nhật"': '"Đã thay thế thành công, nội dung sẽ được cập nhật."',
    'err.message || "Lỗi khi thay thế"': 'err.message || "Không thể thay thế nội dung."',
    'showToast(\n          "Vui lòng bôi đen một từ/cụm từ để sử dụng tính năng đồng nghĩa",\n          "info",\n        )': 'showToast(\n          "Vui lòng bôi đen một từ/cụm từ để sử dụng tính năng đồng nghĩa.",\n          "info",\n        )',
    'showToast(`Gợi ý cho "${targetWord}": ${synonyms.join(", ")}`, "info")': 'showToast(`Gợi ý cho "${targetWord}": ${synonyms.join(", ")}.`, "info")',
    '"Không tìm thấy từ đồng nghĩa phù hợp"': '"Không tìm thấy từ đồng nghĩa phù hợp."',
    'err.message || "Không thể lấy gợi ý lúc này"': 'err.message || "Không thể lấy gợi ý lúc này."',
    '"Không thể tải dữ liệu thanh bên"': '"Không thể tải dữ liệu thanh bên."',
    'showToast(`Cảnh báo logic: ${conflicts[0]}`, "error")': 'showToast(`Cảnh báo logic: ${conflicts[0]}.`, "error")',
    '"Nội dung nhất quán với các chương trước"': '"Nội dung nhất quán với các chương trước."',
    '"Không thể kiểm tra tính nhất quán"': '"Không thể kiểm tra tính nhất quán."',
    '`Đang dịch sang ${targetLang}... Vui lòng đợi`': '`Đang dịch sang ${targetLang}... Vui lòng đợi.`',
    '"Đã dịch thành công"': '"Đã dịch thành công."',
    '"Lỗi dịch thuật: " + err.message': 'err.message || "Lỗi dịch thuật."',
    '"Đã hoàn tác về nguyên bản"': '"Đã hoàn tác về nguyên bản."'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('frontend/features/compilation/components/Editor.tsx', 'w') as f:
    f.write(content)

