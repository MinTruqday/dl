import os
import re

target_dirs = [
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/finance',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/contact'
]

translations = {
    "Giao dịch thất bại. Vui lòng thử lại sau": "Giao dịch thất bại, vui lòng thử lại sau",
    "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau": "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau",
    "Bạn thử quá nhiều lần, vui lòng thử lại sau 5 phút": "Bạn đã thao tác quá nhiều lần, vui lòng thử lại sau 5 phút",
    "Không thể kết nối với hệ thống thanh toán, vui lòng thử lại sau": "Không thể kết nối với hệ thống thanh toán, vui lòng thử lại sau",
    "Không tìm thấy ghi nhận mua này": "Không tìm thấy giao dịch mua tài liệu này",
    "Không thể hoàn tiền vì tác giả đã rút hoặc số dư tác giả không đủ": "Không thể hoàn tiền vì tác giả đã rút tiền hoặc số dư không đủ",
    "Chỉ có thể hoàn tiền trong vòng 48 giờ sau khi mua": "Bạn chỉ được phép hoàn tiền trong vòng 48 giờ kể từ lúc mua",
    "Chỉ có thể hủy yêu cầu đang chờ xử lý": "Chỉ có thể hủy những yêu cầu đang trong trạng thái chờ xử lý",
    "Số dư không đủ để thực hiện yêu cầu rút tiền": "Số dư của bạn không đủ để thực hiện rút tiền",
    "Vượt quá giới hạn rút tiền (tối đa 3 lần/ngày)": "Bạn đã vượt quá giới hạn rút tiền tối đa 3 lần một ngày",
    "Vượt quá hạn mức rút tiền (tối đa 20.000.000 dl/ngày)": "Bạn đã vượt mức rút tiền tối đa 20.000.000 dl trong một ngày",
    "Không thể rút tiền trong vòng 24h sau khi cập nhật thông tin ngân hàng": "Chức năng rút tiền bị khóa trong 24 giờ sau khi cập nhật thông tin ngân hàng",
    "Không thể rút tiền trong vòng 24h sau khi đổi mật khẩu để bảo vệ tài sản": "Chức năng rút tiền bị khóa trong 24 giờ sau khi đổi mật khẩu nhằm bảo vệ tài sản",
    "Hành động xử lý yêu cầu rút tiền không hợp lệ": "Thao tác xử lý yêu cầu rút tiền không hợp lệ",
    "Yêu cầu rút tiền đã được xử lý trước đó": "Yêu cầu rút tiền này đã được hệ thống xử lý",
    "Không thể cập nhật trạng thái yêu cầu": "Không thể cập nhật trạng thái của yêu cầu này",
    "Chỉ quản trị viên mới có thể duyệt mã": "Tính năng duyệt mã chỉ dành riêng cho quản trị viên"
}

total_stripped = 0
total_translated = 0

# Regex to match strings inside detail="", Exception(""), logger.xxx("")
# We will just match any string literal that ends with a dot before the closing quote,
# but it's safer to just process the whole file and find strings that look like typical Vietnamese log sentences ending with '.'
def remove_trailing_periods(text):
    global total_stripped
    # Match any string literal that ends with a period, e.g. "Lỗi hệ thống." or 'Vui lòng thử lại.'
    # It must end with a period followed by the closing quote.
    # We will use a regex to find strings.
    def replacer(m):
        global total_stripped
        quote = m.group(1)
        content = m.group(2)
        if content.endswith('.'):
            # remove trailing period
            content = content[:-1]
            total_stripped += 1
        return quote + content + quote

    # This regex matches simple string literals. It doesn't handle escaped quotes well, but for log messages it's usually fine.
    text = re.sub(r'(["\'])((?:(?!\1)[^\\]|\\.)+)\1', replacer, text)
    return text

for d in target_dirs:
    if os.path.exists(d):
        for root, dirs, files in os.walk(d):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f:
                        content = f.read()
                    
                    original_content = content
                    content = remove_trailing_periods(content)
                    
                    for k, v in translations.items():
                        if k in content:
                            content = content.replace(k, v)
                            total_translated += 1
                            
                    # replace trailing dots in f-strings explicitly if missed
                    # e.g. f"Something." -> f"Something"
                    def f_replacer(m):
                        global total_stripped
                        quote = m.group(1)
                        content = m.group(2)
                        if content.endswith('.'):
                            content = content[:-1]
                            total_stripped += 1
                        return "f" + quote + content + quote
                    content = re.sub(r'f(["\'])((?:(?!\1)[^\\]|\\.)+)\1', f_replacer, content)

                    # Also explicitly check for `. '` or `. "`
                    content = content.replace(".'", "'").replace('."', '"')
                    content = content.replace(". '", " '").replace('. "', ' "')
                    
                    if content != original_content:
                        with open(path, 'w') as f:
                            f.write(content)

print(f"Stripped trailing periods: {total_stripped}")
print(f"Translated phrases: {total_translated}")
