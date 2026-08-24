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
  ACTIVE: "Đang hoạt động",
  APPROVED: "Đã phê duyệt",
  BASELINED: "Đã baseline",
  BLOCKED: "Bị chặn",
  CHANGED: "Đã thay đổi",
  CLOSED: "Đã đóng",
  COMPLETED: "Đã hoàn tất",
  CONFIRMED: "Đã xác nhận",
  DRAFT: "Bản nháp",
  EDITED_ACCEPTED: "Đã chấp nhận sau chỉnh sửa",
  FAIL: "Thất bại",
  IN_PROGRESS: "Đang thực hiện",
  NEEDS_UPDATE: "Cần cập nhật",
  NEW: "Mới",
  OBSOLETE: "Không còn phù hợp",
  PASS: "Đạt",
  PENDING: "Chờ duyệt",
  POTENTIALLY_AFFECTED: "Có thể bị ảnh hưởng",
  READY: "Sẵn sàng",
  REJECTED: "Đã từ chối",
  STALE: "Đã lỗi thời",
  STILL_VALID: "Vẫn hợp lệ",
  SUGGESTED: "AI đề xuất",
};

export function statusLabel(value) {
  return labels[value] || String(value || "Chưa xác định");
}

export function formatDate(value) {
  return value ? new Date(value).toLocaleString("vi-VN") : "Chưa có";
}

export function messageOf(reason) {
  return reason instanceof Error ? reason.message : "Không thể hoàn tất thao tác";
}
