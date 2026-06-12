import os
import re

translations = {
    "DocLib Finance initialized": "Dịch vụ tài chính DocLib đã khởi động",
    "Identity: User {current_user.id} created coupon {coupon.code} with status {status}": "Người dùng {current_user.id} vừa tạo mã giảm giá {coupon.code} với trạng thái {status}",
    "Identity: User {current_user.id} created coupon {coupon_in.code} with status {status}": "Người dùng {current_user.id} vừa tạo mã giảm giá {coupon_in.code} với trạng thái {status}",
    "Invalid signature": "Chữ ký số không hợp lệ",
    "Missing X-User-ID header from API Gateway": "Thiếu thông tin người dùng từ hệ thống cổng API",
    "Missing signature": "Bị thiếu chữ ký số xác thực",
    "Notification failed: {e}": "Không thể gửi thông báo: {e}",
    "payOS webhook missing signature": "Thông báo từ payOS bị thiếu chữ ký xác thực",
    "payOS webhook signature mismatch": "Chữ ký xác thực từ payOS không khớp",
    "Order {order_code} paid amount ({paid_amount}) is less than required ({data.get('amount')}).": "Đơn hàng {order_code} được thanh toán ({paid_amount}) ít hơn số tiền yêu cầu ({data.get('amount')})"
}

target_dirs = [
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/finance',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/contact'
]

total_replacements = 0

for d in target_dirs:
    if os.path.exists(d):
        for root, dirs, files in os.walk(d):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f:
                        content = f.read()
                    
                    changed = False
                    for en, vi in translations.items():
                        if en in content:
                            content = content.replace(en, vi)
                            changed = True
                    
                    # check for `Order {order_code} paid amount ({paid_amount}) is less than required` using regex if slight differences
                    if "is less than required" in content:
                        content = re.sub(
                            r"Order \{order_code\} paid amount \(\{paid_amount\}\) is less than required \(\{.*?\}\)\.",
                            r"Số tiền thanh toán cho đơn hàng {order_code} ({paid_amount}) chưa đủ yêu cầu",
                            content
                        )
                        changed = True
                        
                    # Fix Identity:
                    if "Identity: User " in content:
                        content = re.sub(
                            r"Identity:\s*User\s+\{([^}]+)\}\s+created\s+coupon\s+\{([^}]+)\}\s+with\s+status\s+\{([^}]+)\}",
                            r"Người dùng {\1} vừa tạo mã giảm giá {\2} với trạng thái {\3}",
                            content
                        )
                        changed = True

                    if changed:
                        total_replacements += 1
                        with open(path, 'w') as f:
                            f.write(content)

print(f"Updated {total_replacements} files.")
