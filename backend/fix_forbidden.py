import os

replacements = {
    # "hệ thống"
    "Đã xảy ra lỗi, vui lòng thử lại sau": "Đã xảy ra lỗi, vui lòng thử lại sau",
    "Lỗi xử lý": "Lỗi xử lý",
    "Lỗi khởi tạo quản lý bộ nhớ": "Lỗi khởi tạo quản lý bộ nhớ",
    "Lỗi lưu trữ bản ghi": "Lỗi lưu trữ bản ghi",
    "Đang tải mô hình ngôn ngữ": "Đang tải mô hình ngôn ngữ",
    "Đang xử lý tác vụ": "Đang xử lý tác vụ",
    "Đang sử dụng cấu hình huấn luyện tối ưu": "Đang sử dụng cấu hình huấn luyện tối ưu",
    "Đang sử dụng cấu hình huấn luyện tiêu chuẩn": "Đang sử dụng cấu hình huấn luyện tiêu chuẩn",
    "Lỗi thực thi nội bộ": "Lỗi thực thi nội bộ",
    "Lỗi tìm kiếm thay thế": "Lỗi tìm kiếm thay thế",
    "Lỗi xử lý, đang thử lại": "Lỗi xử lý, đang thử lại",
    "Đang khởi tạo phân mảnh văn bản": "Đang khởi tạo phân mảnh văn bản",
    "Lỗi khởi tạo phân mảnh văn bản, đang dùng chế độ tiêu chuẩn": "Lỗi khởi tạo phân mảnh văn bản, đang dùng chế độ tiêu chuẩn",
    "Lỗi khởi tạo phân mảnh văn bản": "Lỗi khởi tạo phân mảnh văn bản",
    "Không tìm thấy tài liệu": "Không tìm thấy tài liệu",
    "Lỗi tải tệp tin": "Lỗi tải tệp tin",
    "Mô tả chi tiết tác vụ": "Mô tả chi tiết tác vụ",
    "Từ chối thao tác do không đủ quyền": "Từ chối thao tác do không đủ quyền",
    "Từ chối thao tác do quá giới hạn": "Từ chối thao tác do quá giới hạn",
    "Tạm ngừng do lỗi liên tục": "Tạm ngừng do lỗi liên tục",
    "Đang khôi phục hoạt động": "Đang khôi phục hoạt động",
    "Tạm dừng yêu cầu để chống quá tải": "Tạm dừng yêu cầu để chống quá tải",
    "Đang quá tải, vui lòng thử lại sau": "Đang quá tải, vui lòng thử lại sau",
    "Bắt buộc dừng phiên làm việc": "Bắt buộc dừng phiên làm việc",
    "Lỗi điều phối, vui lòng thử lại sau": "Lỗi điều phối, vui lòng thử lại sau",
    "Đã ẩn thông tin cá nhân nhạy cảm": "Đã ẩn thông tin cá nhân nhạy cảm",
    "Tiện ích chưa được đăng ký": "Tiện ích chưa được đăng ký",
    "Lỗi tạo phản hồi": "Lỗi tạo phản hồi",
    "Tắt thu thập dữ liệu thành công": "Tắt thu thập dữ liệu thành công",
    "Lỗi mạng khi lưu tệp vĩnh viễn": "Lỗi mạng khi lưu tệp vĩnh viễn",
    "Lỗi trích xuất tài liệu": "Lỗi trích xuất tài liệu",
    "Lỗi phân tích ngôn ngữ": "Lỗi phân tích ngôn ngữ",
    "Đánh giá khả năng đọc đang bảo trì": "Đánh giá khả năng đọc đang bảo trì",
    "Lỗi tìm kiếm ngữ nghĩa": "Lỗi tìm kiếm ngữ nghĩa",
    "Đang giới hạn yêu cầu, vui lòng thử lại sau": "Đang giới hạn yêu cầu, vui lòng thử lại sau",
    "Lỗi khi biên dịch tài liệu": "Lỗi khi biên dịch tài liệu",
    "Lỗi biên dịch tài liệu": "Lỗi biên dịch tài liệu",
    "Lỗi xuất tài liệu": "Lỗi xuất tài liệu",
    "Lấy nhật ký hoạt động thành công": "Lấy nhật ký hoạt động thành công",
    "Lấy ghi chú kiểm duyệt thành công": "Lấy ghi chú kiểm duyệt thành công",
    "Cập nhật cấu hình cá nhân thành công": "Cập nhật cấu hình cá nhân thành công",
    "Cập nhật cấu hình thành công": "Cập nhật cấu hình thành công",
    "Báo cáo sự cố thành công": "Báo cáo sự cố thành công",
    "Bắt đầu sao lưu dữ liệu": "Bắt đầu sao lưu dữ liệu",
    "Xuất dữ liệu thành công": "Xuất dữ liệu thành công",
    "Lấy cấu hình thành công": "Lấy cấu hình thành công",
    "Lấy trạng thái bảo trì thành công": "Lấy trạng thái bảo trì thành công",
    "Phân công nhiệm vụ thành công": "Phân công nhiệm vụ thành công",

    # "dịch vụ"
    "Chưa cấu hình tính năng gửi email": "Chưa cấu hình tính năng gửi email",
    "Đăng ký AI thành công": "Đăng ký AI thành công",
    "Tính năng thu thập dữ liệu đã sẵn sàng": "Tính năng thu thập dữ liệu đã sẵn sàng",
    "Lỗi vượt tường lửa": "Lỗi vượt tường lửa",
    "Quản lý nội dung đã sẵn sàng": "Quản lý nội dung đã sẵn sàng",
    "Tính năng xuất PDF đang bảo trì": "Tính năng xuất PDF đang bảo trì",
    "Lỗi tìm kiếm thông minh": "Lỗi tìm kiếm thông minh",
    "Tính năng thanh toán đã sẵn sàng": "Tính năng thanh toán đã sẵn sàng",
    "Tính năng thanh toán đang bảo trì, vui lòng thử lại sau": "Tính năng thanh toán đang bảo trì, vui lòng thử lại sau",
    "Tính năng thanh toán đang bảo trì": "Tính năng thanh toán đang bảo trì",
    "Giao dịch thanh toán đang gặp lỗi": "Giao dịch thanh toán đang gặp lỗi",
    "Đã xảy ra lỗi, vui lòng thử lại sau": "Đã xảy ra lỗi, vui lòng thử lại sau",
    "Khởi tạo biên dịch thành công": "Khởi tạo biên dịch thành công",
    "Lỗi kết nối AI": "Lỗi kết nối AI",
    "Kiểm tra bản gốc đang gặp sự cố": "Kiểm tra bản gốc đang gặp sự cố",
    "Lỗi phân tích ngữ pháp": "Lỗi phân tích ngữ pháp",
    "Khởi tạo thông báo thành công": "Khởi tạo thông báo thành công",
    "Từ chối yêu cầu xác thực": "Từ chối yêu cầu xác thực",
    "Lỗi kết nối quản lý người dùng": "Lỗi kết nối quản lý người dùng",

    # "an toàn"
    "Lỗi tạo liên kết tải xuống bảo mật": "Lỗi tạo liên kết tải xuống bảo mật",
    "Lỗi tạo liên kết truy cập bảo mật": "Lỗi tạo liên kết truy cập bảo mật",
    "Tệp có rủi ro bảo mật": "Tệp có rủi ro bảo mật",
    "Từ chối tệp đồ họa vector do có rủi ro": "Từ chối tệp đồ họa vector do có rủi ro",
    "Đang đóng kết nối hàng đợi tin nhắn": "Đang đóng kết nối hàng đợi tin nhắn",
    "Lỗi trích xuất liên kết tải xuống": "Lỗi trích xuất liên kết tải xuống",

    # "cơ chế"
    # Actually need to check if there are any "cơ chế"
    "Lỗi cấu hình": "Lỗi cấu hình",

    # "toàn cầu"
    "Cập nhật cấu hình bảo trì thành công": "Cập nhật cấu hình bảo trì thành công",

    # "chức năng"
    "Tạo tài khoản tạm thời bị vô hiệu hóa": "Tạo tài khoản tạm thời bị vô hiệu hóa",
    "Không có quyền thực hiện thao tác này": "Không có quyền thực hiện thao tác này",
}

def replace_in_files():
    total_replaced = 0
    for root, _, files in os.walk('.'):
        if 'venv' in root or 'node_modules' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original_content = content
                for old, new in replacements.items():
                    content = content.replace(f'"{old}"', f'"{new}"')
                    content = content.replace(f"'{old}'", f"'{new}'")
                
                if content != original_content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    total_replaced += 1
    print(f"Total files updated: {total_replaced}")

if __name__ == "__main__":
    replace_in_files()

replacements.update({
    "Tính năng cung cấp đã sẵn sàng": "Tính năng cung cấp đã sẵn sàng",
    "Thay đổi trạng thái bảo trì thành công": "Thay đổi trạng thái bảo trì thành công",
    "Cập nhật cấu hình bảo trì thành công": "Cập nhật cấu hình bảo trì thành công",
    "Lỗi lấy dữ liệu thống kê": "Lỗi lấy dữ liệu thống kê",
    "Từ chối yêu cầu thu thập": "Từ chối yêu cầu thu thập",
    "Lỗi kết nối bộ thu thập dữ liệu": "Lỗi kết nối bộ thu thập dữ liệu",
    "Ghi nhận báo cáo lỗi thành công": "Ghi nhận báo cáo lỗi thành công",
    "Từ chối yêu cầu do điều kiện không hợp lệ": "Từ chối yêu cầu do điều kiện không hợp lệ",
    "Lỗi xử lý từ chối yêu cầu": "Lỗi xử lý từ chối yêu cầu",
    "Ghi nhận thao tác thành công": "Ghi nhận thao tác thành công",
    "Lỗi gửi thông báo bên ngoài": "Lỗi gửi thông báo bên ngoài",
    "Ghi nhận sự kiện thành công": "Ghi nhận sự kiện thành công",
    "Tạo báo cáo tình trạng thành công": "Tạo báo cáo tình trạng thành công",
    "Lấy thống kê hiệu suất thành công": "Lấy thống kê hiệu suất thành công",
    "Hoàn tất kiểm tra": "Hoàn tất kiểm tra",
    "Lấy nhật ký thành công": "Lấy nhật ký thành công",
    "Cập nhật giới hạn tài nguyên thành công": "Cập nhật giới hạn tài nguyên thành công",
    "Lấy cấu hình tài nguyên thành công": "Lấy cấu hình tài nguyên thành công",
    "Tính năng tin nhắn đã sẵn sàng": "Tính năng tin nhắn đã sẵn sàng",
    "Khởi tạo tin nhắn thành công": "Khởi tạo tin nhắn thành công",
    "Tính năng đang được bảo trì": "Tính năng đang được bảo trì",
    "Lỗi khởi tạo do thiếu kết nối cơ sở dữ liệu": "Lỗi khởi tạo do thiếu kết nối cơ sở dữ liệu",
    "Mất kết nối với máy chủ": "Mất kết nối với máy chủ",
    "Từ chối truy cập do không đủ ủy quyền": "Từ chối truy cập do không đủ ủy quyền",
    "Tính năng xác thực đã sẵn sàng": "Tính năng xác thực đã sẵn sàng",
    "Chưa cấu hình xác thực bên ngoài": "Chưa cấu hình xác thực bên ngoài",
    "Lỗi kết nối tài khoản": "Lỗi kết nối tài khoản",
    "Lỗi xác thực liên kết": "Lỗi xác thực liên kết",
    "Xác thực liên kết thành công": "Xác thực liên kết thành công",
    "Khởi tạo AI thành công": "Khởi tạo AI thành công",
    "Lỗi xử lý nội bộ": "Lỗi xử lý nội bộ",
    "Lỗi kết nối nền": "Lỗi kết nối nền",
})

if __name__ == "__main__":
    replace_in_files()
