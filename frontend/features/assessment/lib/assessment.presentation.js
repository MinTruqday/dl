const statusLabels = {
  active: "Đang làm",
  archived: "Đã lưu trữ",
  completed: "Đã hoàn tất",
  draft: "Bản nháp",
  expired: "Đã hết hạn",
  failed: "Thất bại",
  indexed: "Đã lập chỉ mục",
  indexing: "Đang lập chỉ mục",
  needs_review: "Cần rà soát",
  pending: "Đang chờ",
  pending_manual_scoring: "Chờ chấm thủ công",
  published: "Đã xuất bản",
  queued: "Đang chờ xử lý",
  ready: "Sẵn sàng",
  rejected: "Đã từ chối",
  scheduled: "Đã lên lịch",
  scored: "Đã chấm",
  stopped: "Đã dừng",
  submitted: "Đã nộp",
  timed_out: "Hết thời gian",
  unavailable: "Không sẵn sàng",
  upcoming: "Sắp mở",
};

const subjectLabels = {
  biology: "Sinh học",
  chemistry: "Hóa học",
  english: "Tiếng Anh",
  history: "Lịch sử",
  literature: "Ngữ văn",
  math: "Toán",
  physics: "Vật lý",
};

export function labelStatus(value, fallback = "Chưa xác định") {
  return statusLabels[String(value || "").toLowerCase()] || value || fallback;
}

export function labelSubject(value) {
  return subjectLabels[String(value || "").toLowerCase()] || value || "Chưa gắn môn";
}

export function formatDateTime(value, fallback = "Chưa có") {
  if (!value) return fallback;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? fallback : date.toLocaleString("vi-VN");
}

export function finishedAttempt(item) {
  return ["submitted", "completed", "timed_out"].includes(item?.attempt?.status || "");
}

export function assignmentStatus(item) {
  if (item?.status === "pending_manual_scoring") return "Chờ chấm thủ công";
  if (item?.status === "scored") return "Đã chấm";
  if (item?.attempt?.status === "active") return "Đang làm";
  return labelStatus(item?.availability_status, "Có thể làm");
}
