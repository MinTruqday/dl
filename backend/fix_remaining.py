import os
import re

replacements = {
    "provision/src/services/operation_service.py": [
        (r'f"The access privileges for the user account associated with identifier \{[^\}]+\} have been successfully modified to the requested role"', r'"Cập nhật quyền truy cập tài khoản thành công"'),
        (r'f"The operational activity status for the user account associated with identifier \{[^\}]+\} has been updated to reflect the new state"', r'"Cập nhật trạng thái hoạt động tài khoản thành công"'),
    ],
    "websocket/src/services/editor_ws_service.py": [
        (r'f"A new device has successfully established a connection to the collaboration space with identifier \{[^\}]+\} bringing the total active sessions to \{[^\}]+\}"', r'"Thiết bị mới đã kết nối vào không gian cộng tác"'),
        (r'f"A device has cleanly disconnected from the collaboration space with identifier \{[^\}]+\}"', r'"Thiết bị đã ngắt kết nối khỏi không gian cộng tác"'),
        (r'f"The system encountered an unexpected network failure while attempting to broadcast synchronization signals to the collaboration space with identifier \{[^\}]+\}"', r'"Lỗi đồng bộ dữ liệu trong không gian cộng tác"'),
    ],
    "websocket/src/router/message_ws_router.py": [
        (r'f"The system failed to authenticate the connection token for the user with identifier \{[^\}]+\} due to an invalid or expired payload"', r'"Lỗi xác thực kết nối do mã thông báo không hợp lệ hoặc đã hết hạn"'),
        (r'f"The system encountered an unexpected error while processing direct messages for the user with identifier \{[^\}]+\}"', r'"Lỗi xử lý tin nhắn trực tiếp"'),
    ],
    "websocket/src/router/editor_ws_router.py": [
        (r'f"The real-time data connection failed unexpectedly while synchronizing the document with identifier \{[^\}]+\}"', r'"Lỗi kết nối dữ liệu theo thời gian thực"'),
    ],
    "security/src/services/auth_service.py": [
        (r'f"A new user account with the email address \{[^\}]+\} was successfully registered from the network address \{[^\}]+\}"', r'"Đăng ký tài khoản mới thành công"'),
        (r'f"An authentication attempt for the account \{[^\}]+\} failed due to incorrect credentials from the network address \{[^\}]+\}"', r'"Đăng nhập thất bại do sai thông tin xác thực"'),
        (r'f"The account associated with \{[^\}]+\} has successfully authenticated from the network address \{[^\}]+\}"', r'"Đăng nhập thành công"'),
        (r'f"All active authentication sessions for the account associated with the identifier \{[^\}]+\} have been successfully revoked"', r'"Đã thu hồi tất cả phiên đăng nhập của tài khoản"'),
        (r'f"The password for the account associated with \{[^\}]+\} was successfully modified from the network address \{[^\}]+\}"', r'"Đổi mật khẩu thành công"'),
        (r'f"A new integrated account was automatically provisioned for the email address \{[^\}]+\} following a successful external authentication"', r'"Tự động tạo tài khoản liên kết thành công"'),
    ],
    "security/src/services/email_service.py": [
        (r'f"The system is initiating the dispatch process for a password recovery email to the address \{[^\}]+\}"', r'"Đang gửi email khôi phục mật khẩu"'),
        (r'f"The email dispatch process for the address \{[^\}]+\} could not proceed due to incomplete or missing mailing service configurations"', r'"Chưa cấu hình tính năng gửi email"'),
        (r'f"The password recovery instructions were successfully transmitted to the email address \{[^\}]+\}"', r'"Gửi hướng dẫn khôi phục mật khẩu thành công"'),
    ],
    "security/src/services/passkey_service.py": [
        (r'f"The system was unable to clear the consumed authentication challenge for the account \{[^\}]+\} from the cache"', r'"Lỗi xóa mã xác thực khỏi bộ nhớ"'),
    ],
    "agentic_ai/src/utils/resilience.py": [
        (r'f"Operation failed permanently after \{[^\}]+\} retry attempts"', r'"Thao tác thất bại sau nhiều lần thử lại"'),
    ],
    "agentic_ai/src/workflow/graph.py": [
        (r'f"Cache initialization failed: \{[^\}]+\}"', r'"Lỗi khởi tạo bộ nhớ đệm"'),
    ],
    "content/src/core/publication.py": [
        (r'f"Failed to publish event to \{[^\}]+\}"', r'"Lỗi xuất bản sự kiện"'),
    ],
    "content/src/router/dependency_router.py": [
        (r'f"Failed to verify storage quota from provision subsystem: \{[^\}]+\}"', r'"Lỗi xác minh dung lượng lưu trữ"'),
    ],
    "finance/src/services/purchase_service.py": [
        (r'f"Your account already has an active \{[^\}]+\} membership plan."', r'"Tài khoản đã có gói thành viên này"'),
        (r'f"Insufficient balance. This membership plan requires \{[^\}]+\} dl."', r'"Số dư không đủ để đăng ký gói thành viên"'),
        (r'f"User \{[^\}]+\} upgraded membership to \{[^\}]+\} tier"', r'"Nâng cấp gói thành viên thành công"'),
        (r'f"Membership upgrade failed for user \{[^\}]+\}"', r'"Lỗi nâng cấp gói thành viên"'),
    ],
    "worker/src/tasks.py": [
        (r'f"Initiating the permanent removal process for the document with identifier \{[^\}]+\}"', r'"Đang bắt đầu quá trình xóa vĩnh viễn tài liệu"'),
        (r'f"The document with identifier \{[^\}]+\} has been permanently removed from the storage system"', r'"Xóa vĩnh viễn tài liệu thành công"'),
        (r'f"Failed to complete the permanent removal process for the document with identifier \{[^\}]+\} due to an unexpected network or system failure"', r'"Lỗi xóa vĩnh viễn tài liệu"'),
        (r'f"Initiating the compilation process for the document with identifier \{[^\}]+\}"', r'"Đang bắt đầu quá trình biên dịch tài liệu"'),
        (r'f"Executing the underlying compilation steps for the document with identifier \{[^\}]+\}"', r'"Đang thực thi biên dịch tài liệu"'),
        (r'f"The compilation process failed to generate the final output for the document with identifier \{[^\}]+\}"', r'"Lỗi biên dịch, không thể tạo kết quả cuối cùng"'),
        (r'f"The document with identifier \{[^\}]+\} has been successfully compiled and processed"', r'"Biên dịch tài liệu thành công"'),
        (r'f"The background compilation process exceeded the maximum allowed execution time for the document with identifier \{[^\}]+\}"', r'"Quá thời gian biên dịch tài liệu"'),
        (r'f"An unexpected system failure occurred while attempting to compile the document with identifier \{[^\}]+\}"', r'"Lỗi khi biên dịch tài liệu"'),
    ]
}

for path, patterns in replacements.items():
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig_content = content
    for old_pat, new_str in patterns:
        content = re.sub(old_pat, new_str, content)
        
    if content != orig_content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")
    else:
        print(f"No changes in {path}")
