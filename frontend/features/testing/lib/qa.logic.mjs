export function emptyDoc() {
  return { type: "doc", content: [] };
}

export function textDoc(text) {
  return {
    type: "doc",
    content: text ? [{ type: "paragraph", content: [{ type: "text", text: String(text) }] }] : [],
  };
}

export function docText(document) {
  const values = [];
  const visit = (node) => {
    if (Array.isArray(node)) return node.forEach(visit);
    if (!node || typeof node !== "object") return;
    if (typeof node.text === "string") values.push(node.text);
    if (node.content) visit(node.content);
  };
  visit(document);
  return values.join(" ").trim();
}

const labels = {
  ACCEPTED: "Đã chấp nhận",
  ACTIVE: "Đang hoạt động",
  APPLY_PARTIAL: "Áp dụng một phần",
  APPROVED: "Đã phê duyệt",
  ARCHIVED: "Đã lưu trữ",
  BASELINED: "Đã đặt làm phiên bản chuẩn",
  BLOCKED: "Bị chặn",
  CHANGED: "Đã thay đổi",
  CLOSED: "Đã đóng",
  COMPLETED: "Đã hoàn tất",
  CONFIRMED: "Đã xác nhận",
  DEGRADED: "Hoạt động giới hạn",
  DUPLICATE: "Trùng lặp",
  DRAFT: "Bản nháp",
  EDITED_ACCEPTED: "Đã chấp nhận sau chỉnh sửa",
  FAIL: "Thất bại",
  FAILED: "Không thành công",
  IN_REVIEW: "Đang chờ duyệt",
  IN_PROGRESS: "Đang thực hiện",
  MUST_RUN: "Bắt buộc chạy",
  NEEDS_UPDATE: "Cần cập nhật",
  NEW: "Mới",
  NORMAL: "Bình thường",
  NOT_APPLICABLE: "Không áp dụng",
  NOT_RUN: "Chưa chạy",
  OBSOLETE: "Không còn phù hợp",
  OPTIONAL: "Không bắt buộc",
  PASS: "Đạt",
  PARTIAL_EXECUTION: "Thực thi một phần",
  PENDING: "Chờ duyệt",
  POTENTIALLY_AFFECTED: "Có thể bị ảnh hưởng",
  READY: "Sẵn sàng",
  READY_FOR_RETEST: "Sẵn sàng kiểm thử lại",
  REJECTED: "Đã từ chối",
  REOPENED: "Đã mở lại",
  RESOLVED: "Đã xử lý",
  SHOULD_RUN: "Nên chạy",
  SKIPPED: "Đã bỏ qua",
  STALE: "Đã lỗi thời",
  STILL_VALID: "Vẫn hợp lệ",
  SUCCESS: "Thành công",
  SUGGESTED: "AI đề xuất",
  UNCHANGED: "Không thay đổi",
};

const valueLabels = {
  api: "API",
  blocker: "Chặn toàn bộ",
  boundary: "Giá trị biên",
  business_rule: "Quy tắc nghiệp vụ",
  concurrency: "Xử lý đồng thời",
  critical: "Nghiêm trọng",
  custom: "Tùy chỉnh",
  data_persistence: "Lưu trữ dữ liệu",
  error_handling: "Xử lý lỗi",
  feature: "Theo tính năng",
  functional: "Chức năng",
  happy_path: "Luồng thành công",
  high: "Cao",
  integration: "Tích hợp",
  low: "Thấp",
  major: "Lớn",
  medium: "Trung bình",
  minor: "Nhỏ",
  negative: "Tình huống lỗi",
  non_functional: "Phi chức năng",
  permission: "Phân quyền",
  regression: "Hồi quy",
  smoke: "Kiểm tra nhanh",
  state_transition: "Chuyển trạng thái",
  trivial: "Không đáng kể",
  ui: "Giao diện",
  validation: "Xác thực dữ liệu",
};

export function statusLabel(value) {
  return labels[value] || String(value || "Chưa xác định");
}

export function valueLabel(value) {
  return valueLabels[value] || statusLabel(value);
}

export function formatDate(value) {
  return value ? new Date(value).toLocaleString("vi-VN") : "Chưa có";
}

export function messageOf(reason) {
  return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}
