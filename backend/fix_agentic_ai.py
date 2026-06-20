import os
import re

vi_to_en = {
    "Lỗi xử lý, vui lòng thử lại sau": "Processing error, please retry",
    "Đã xảy ra lỗi, vui lòng thử lại sau": "Error occurred, please retry",
    "Lỗi xử lý": "Processing error",
    "Lỗi khởi tạo quản lý bộ nhớ": "Memory manager init failed",
    "Lỗi lưu trữ bản ghi": "Record storage failed",
    "Đang tải mô hình ngôn ngữ": "Loading language model",
    "Đang xử lý tác vụ": "Processing task",
    "Đang sử dụng cấu hình huấn luyện tối ưu": "Using optimal training config",
    "Đang sử dụng cấu hình huấn luyện tiêu chuẩn": "Using standard training config",
    "Lỗi thực thi nội bộ": "Internal execution error",
    "Lỗi tìm kiếm thay thế": "Fallback search failed",
    "Lỗi xử lý, đang thử lại": "Processing error, retrying",
    "Đang khởi tạo phân mảnh văn bản": "Initializing text chunker",
    "Lỗi khởi tạo phân mảnh văn bản, đang dùng chế độ tiêu chuẩn": "Text chunker init failed, using standard mode",
    "Lỗi khởi tạo phân mảnh văn bản": "Text chunker init failed",
    "Không tìm thấy tài liệu": "Document not found",
    "Lỗi tải tệp tin": "File load failed",
    "Mô tả chi tiết tác vụ": "Detailed task description",
    "Từ chối thao tác do không đủ quyền": "Operation denied: insufficient permissions",
    "Từ chối thao tác do quá giới hạn": "Operation denied: quota exceeded",
    "Tạm ngừng do lỗi liên tục": "Paused due to continuous errors",
    "Đang khôi phục hoạt động": "Recovering operation",
    "Tạm dừng yêu cầu để chống quá tải": "Paused to prevent overload",
    "Đang quá tải, vui lòng thử lại sau": "System overloaded, please retry",
    "Bắt buộc dừng phiên làm việc": "Session forcefully stopped",
    "Lỗi điều phối, vui lòng thử lại sau": "Orchestration error, please retry",
    "Đã ẩn thông tin cá nhân nhạy cảm": "Sensitive info masked",
    "Đăng ký AI thành công": "Tool registered successfully",
    "Tiện ích chưa được đăng ký": "Tool not registered",
    "Lỗi xử lý nội bộ": "Internal processing error",
    "Lỗi tạo phản hồi": "Response generation failed",
    "Lỗi đưa dữ liệu tìm kiếm vào hàng đợi": "Failed to enqueue search data",
    "Lỗi khởi tạo danh sách chỉ mục tìm kiếm": "Search index init failed",
    "Lỗi xử lý tìm kiếm": "Search processing failed",
    "Lỗi xóa dữ liệu chỉ mục tìm kiếm": "Failed to delete search index",
    "Lỗi hệ thống, vui lòng thử lại sau": "System error, please retry",
    "Đã xảy ra lỗi, vui lòng thử lại sau": "Error occurred, please retry",
}

long_en_to_short_en = {
    "Authentication is required to view the transaction history please log in and try again": "Authentication required to view transaction history",
    "There are no recent transactions associated with this account": "No recent transactions found",
    "The system encountered an error while attempting to load the transaction history": "Failed to load transaction history",
    "Authentication is required to redeem the gift code please log in and try again": "Authentication required to redeem gift code",
    "The provided gift code is invalid or has already been redeemed": "Gift code invalid or already redeemed",
    "The gift code redemption process failed due to an unexpected issue": "Gift code redemption failed",
    "Authentication is required to view the revenue report please log in and try again": "Authentication required to view revenue report",
    "The system was unable to retrieve the revenue reporting data": "Failed to retrieve revenue data",
    "Authentication is required to view the document library please log in and try again": "Authentication required to view document library",
    "There are no available documents within your personal library": "No documents in library",
    "The system encountered an error while fetching the document list": "Failed to fetch document list",
    "Authentication is required to perform this action": "Authentication required",
    "Your account does not possess the necessary authorization to access this specific area": "Access denied: insufficient authorization",
    "The document trash bin is currently empty": "Trash bin is empty",
    "The system encountered an error while accessing the document trash bin": "Failed to access trash bin",
    "Authentication is required to delete the document please log in and try again": "Authentication required to delete document",
    "The specified document was deleted successfully": "Document deleted successfully",
    "The system failed to delete the specified document": "Failed to delete document",
    "The specified document was restored successfully": "Document restored successfully",
    "The document restoration process failed": "Document restoration failed",
    "Your account does not possess the necessary authorization to perform this operation": "Operation denied: insufficient authorization",
    "The system was unable to retrieve the statistical analysis data": "Failed to retrieve statistical data",
    "The specified document content could not be located": "Document content not found",
    "Authentication is required to initiate the deposit process please log in and try again": "Authentication required to initiate deposit",
    "The system was unable to generate the required payment link": "Failed to generate payment link",
    "The payment initialization process encountered an unexpected failure": "Payment initialization failed",
    "The document was created successfully however the system could not retrieve the access identifier": "Document created but identifier unavailable",
    "The system failed to create the new document due to an unexpected internal error": "Failed to create document",
    "The system was unable to retrieve the requested document information": "Failed to retrieve document info",
    "The operation failed due to a security restriction or the document does not exist": "Operation failed: security restriction or document missing",
    "No modifications were made to the document information": "No modifications made to document",
    "The specified document contains no text to process for translation": "Document contains no text for translation",
    "The artificial intelligence translation service encountered an unexpected failure": "Translation service failed",
    "The system encountered an error during the translation process": "Translation process failed",
    "The system could not generate a translated version of the text": "Failed to generate translation",
    "The translation was generated successfully however the system could not retrieve the new file identifier": "Translation generated but file identifier unavailable",
    "The translation was generated successfully but the system failed to save the new file": "Translation generated but save failed",
    "The system encountered an error while attempting to create the new translated document": "Failed to create translated document",
    "The execution process exceeded the maximum allowed time limit and was terminated": "Execution exceeded time limit and terminated",
    "The system encountered an unexpected error during execution and requires you to try again later": "Execution error, please retry",
    "The submitted request violates network security protocols and has been blocked": "Request blocked: violates security protocols",
    "The system could not locate any relevant information from the available search sources": "No relevant info found from search sources",
    "Authentication is required to proceed with this specific operation": "Authentication required",
    "The system could not identify a suitable utility to process the given request": "No suitable utility found",
    "The requested utility could not be found within the available system resources": "Requested utility not found",
    "The requested operation requires explicit user authorization before proceeding": "Explicit user authorization required",
    "The operation failed to complete successfully after exhausting all available retry attempts": "Operation failed after retries",
    "The system encountered an unexpected error during the execution phase and requires you to try again later": "Execution error, please retry",
    "The system encountered an error during the inference process": "Inference process error",
    "The system could not locate any matching documents within the knowledge base": "No matching documents found in knowledge base",
    "The system encountered an unexpected error during data retrieval and requires you to try again later": "Data retrieval error, please retry",
    "The response was blocked by the security system due to the detection of sensitive information": "Response blocked: sensitive info detected",
    "Authentication is required to proceed with this operation please ensure you are logged in": "Authentication required",
    "The specified document content could not be located in the system": "Document content not found",
}

def replace_in_file(path, replacements, require_vi=False):
    if not os.path.exists(path):
        return False
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig_content = content
    for old, new in replacements.items():
        if require_vi and 'router' in path and 'agentic_ai' in path:
            continue
        content = content.replace(f'"{old}"', f'"{new}"')
        content = content.replace(f"'{old}'", f"'{new}'")
        content = content.replace(f'f"{old}"', f'f"{new}"')
        content = content.replace(f"f'{old}'", f"f'{new}'")
        
    if content != orig_content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

total = 0
for root, _, files in os.walk('agentic_ai'):
    if 'venv' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            if replace_in_file(path, vi_to_en, require_vi=True):
                print(f"Updated vi->en in {path}")
            if replace_in_file(path, long_en_to_short_en, require_vi=False):
                print(f"Updated en->en in {path}")
                total += 1

print(f"Done.")
