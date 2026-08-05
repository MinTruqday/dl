"use client";

import { useEffect, useState } from "react";
import {
  FileVersionItem,
  ProtectedShareResult,
  QuotaAnalyticsData,
  StorageItem,
  getFileVersionsAPI,
  getItemActivitiesAPI,
  getStorageQuotaAnalyticsAPI,
} from "@/features/cloud/services/storage.service";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import {
  BarChart3,
  Check,
  Clock,
  Code,
  Copy,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Film,
  History,
  Image as ImageIcon,
  Music,
  Palette,
  RotateCcw,
  RotateCw,
  Tag,
  Trash2,
  Upload,
  User,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

function formatBytes(bytes: number) {
  if (!bytes || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
}

export function StorageTextModal({
  open,
  close,
  title,
  label,
  initialValue = "",
  processing,
  submit,
}: {
  open: boolean;
  close: () => void;
  title: string;
  label: string;
  initialValue?: string;
  processing: boolean;
  submit: (value: string) => Promise<boolean>;
}) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue, open]);

  const save = async () => {
    if (await submit(value)) {
      setValue("");
      close();
    }
  };

  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>{title}</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="storage-text"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          {label}
        </label>
        <input
          id="storage-text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="apple-input w-full"
          autoFocus
        />
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={!value.trim() || processing} onClick={save}>
          {processing ? "Đang lưu..." : "Lưu"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function StorageShareModal({
  item,
  close,
  processing,
  submit,
  revokeShare,
  createLink,
}: {
  item: StorageItem | null;
  close: () => void;
  processing: boolean;
  submit: (email: string, role: string) => Promise<boolean>;
  revokeShare?: (targetUserId: string) => Promise<boolean>;
  createLink: (
    password: string,
    expiresInHours: number
  ) => Promise<ProtectedShareResult>;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [password, setPassword] = useState("");
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [link, setLink] = useState("");
  const [linkError, setLinkError] = useState("");
  const [creatingLink, setCreatingLink] = useState(false);

  const save = async () => {
    if (await submit(email, role)) {
      setEmail("");
    }
  };

  const generateLink = async () => {
    setCreatingLink(true);
    setLinkError("");
    try {
      const result = await createLink(password, expiresInHours);
      setLink(`${window.location.origin}/chia-se/${result.share_token}`);
    } catch (cause) {
      setLinkError(
        cause instanceof Error ? cause.message : "Không thể tạo liên kết"
      );
    } finally {
      setCreatingLink(false);
    }
  };

  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <ModalTitle>Chia sẻ &quot;{item?.name}&quot;</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-6">
          {/* Internal User Share */}
          <section className="space-y-3">
            <p className="text-[13px] font-semibold text-ink">
              Chia sẻ nội bộ với người dùng
            </p>
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="email"
                  placeholder="Nhập email người nhận..."
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="apple-input w-full"
                />
              </div>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="apple-input w-28"
              >
                <option value="viewer">Xem</option>
                <option value="editor">Chỉnh sửa</option>
              </select>
              <Button
                disabled={!email.trim() || processing}
                onClick={save}
              >
                {processing ? "..." : "Thêm"}
              </Button>
            </div>

            {/* List of currently shared users */}
            {item?.shared_with && item.shared_with.length > 0 && (
              <div className="mt-3 space-y-2 rounded-xl bg-surface-muted p-3">
                <p className="text-[12px] font-medium text-ink-muted">
                  Người đã được cấp quyền:
                </p>
                <div className="space-y-1.5">
                  {item.shared_with.map((member) => (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between rounded-lg bg-surface px-3 py-1.5 text-xs shadow-xs"
                    >
                      <div className="flex items-center gap-2">
                        <User className="h-3.5 w-3.5 text-ink-muted" />
                        <span className="font-medium text-ink">
                          {member.user_id}
                        </span>
                        <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                          {member.role === "editor" ? "Chỉnh sửa" : "Xem"}
                        </span>
                      </div>
                      {revokeShare && (
                        <button
                          type="button"
                          onClick={() => revokeShare(member.user_id)}
                          className="text-danger hover:underline text-[11px]"
                        >
                          Thu hồi
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* Public Link Share */}
          <section className="space-y-4 border-t border-border pt-5">
            <p className="text-[13px] font-semibold text-ink">
              Tạo liên kết chia sẻ ngoài
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-[12px] text-ink-muted">
                  Mật khẩu bảo vệ (tùy chọn)
                </label>
                <input
                  type="password"
                  minLength={6}
                  placeholder="Tối thiểu 6 ký tự"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="apple-input w-full text-xs"
                />
              </div>
              <div>
                <label className="mb-1 block text-[12px] text-ink-muted">
                  Thời hạn hiệu lực
                </label>
                <select
                  value={expiresInHours}
                  onChange={(e) => setExpiresInHours(Number(e.target.value))}
                  className="apple-input w-full text-xs"
                >
                  <option value={24}>24 giờ</option>
                  <option value={72}>3 ngày</option>
                  <option value={168}>7 ngày</option>
                  <option value={720}>30 ngày</option>
                </select>
              </div>
            </div>

            {linkError && (
              <p className="text-[12px] text-danger">{linkError}</p>
            )}

            {link && (
              <div className="flex gap-2">
                <input
                  readOnly
                  value={link}
                  className="apple-input min-w-0 flex-1 text-xs"
                />
                <Button
                  variant="secondary"
                  onClick={() => navigator.clipboard.writeText(link)}
                >
                  Sao chép
                </Button>
              </div>
            )}

            <Button
              variant="secondary"
              disabled={
                creatingLink || (password.length > 0 && password.length < 6)
              }
              onClick={generateLink}
              className="w-full"
            >
              {creatingLink ? "Đang tạo liên kết..." : "Tạo liên kết công khai"}
            </Button>
          </section>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Đóng
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function StorageVersionModal({
  item,
  close,
  onRollback,
  onUploadNew,
  processing,
}: {
  item: StorageItem | null;
  close: () => void;
  onRollback: (versionId: string) => Promise<boolean>;
  onUploadNew?: () => void;
  processing: boolean;
}) {
  const [versions, setVersions] = useState<FileVersionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!item || item.is_folder) return;
    setLoading(true);
    setError("");
    getFileVersionsAPI(item._id)
      .then(setVersions)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Lỗi khi tải phiên bản")
      )
      .finally(() => setLoading(false));
  }, [item]);

  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-primary" />
          <ModalTitle>Lịch sử phiên bản: {item?.name}</ModalTitle>
        </div>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-ink-muted">
              Lưu giữ tối đa 10 phiên bản gần nhất
            </span>
            {onUploadNew && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  close();
                  onUploadNew();
                }}
              >
                <Upload className="mr-1 h-3.5 w-3.5" />
                Tải lên bản mới
              </Button>
            )}
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-ink-muted">
              Đang tải lịch sử phiên bản...
            </div>
          ) : error ? (
            <div className="rounded-lg bg-danger/10 p-3 text-xs text-danger">
              {error}
            </div>
          ) : (
            <div className="space-y-2.5">
              {versions.map((ver, idx) => (
                <div
                  key={ver.version_id || idx}
                  className={`flex items-center justify-between rounded-xl border p-3 transition-colors ${
                    ver.is_active
                      ? "border-primary/40 bg-primary/5"
                      : "border-border bg-surface"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-ink">
                        {ver.is_active
                          ? "Phiên bản hiện tại"
                          : `Phiên bản #${versions.length - idx}`}
                      </span>
                      {ver.is_active && (
                        <span className="rounded bg-primary px-1.5 py-0.2 text-[10px] font-bold text-white">
                          Đang dùng
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-ink-muted">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(ver.created_at).toLocaleString("vi-VN")}
                      </span>
                      <span>•</span>
                      <span>{formatBytes(ver.size)}</span>
                    </div>
                  </div>

                  {!ver.is_active && (
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={processing}
                      onClick={() => onRollback(ver.version_id)}
                      className="text-xs"
                    >
                      <RotateCcw className="mr-1 h-3.5 w-3.5" />
                      Khôi phục
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Đóng
        </Button>
      </ModalFooter>
    </Modal>
  );
}

const PALETTE_COLORS = [
  { name: "Mặc định", value: "" },
  { name: "Đỏ", value: "#EF4444" },
  { name: "Cam", value: "#F97316" },
  { name: "Vàng", value: "#F59E0B" },
  { name: "Xanh lá", value: "#10B981" },
  { name: "Xanh dương", value: "#3B82F6" },
  { name: "Tím", value: "#8B5CF6" },
  { name: "Hồng", value: "#EC4899" },
  { name: "Xám", value: "#64748B" },
];

export function StorageTagColorModal({
  item,
  close,
  onSave,
  processing,
}: {
  item: StorageItem | null;
  close: () => void;
  onSave: (tags: string[], color?: string) => Promise<boolean>;
  processing: boolean;
}) {
  const [tags, setTags] = useState<string[]>([]);
  const [inputTag, setInputTag] = useState("");
  const [color, setColor] = useState<string>("");

  useEffect(() => {
    if (item) {
      setTags(item.tags || []);
      setColor(item.color || "");
    }
  }, [item]);

  const addTag = () => {
    const trimmed = inputTag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setInputTag("");
    }
  };

  const removeTag = (t: string) => {
    setTags(tags.filter((x) => x !== t));
  };

  const save = async () => {
    if (await onSave(tags, color)) {
      close();
    }
  };

  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <div className="flex items-center gap-2">
          <Tag className="h-5 w-5 text-primary" />
          <ModalTitle>Gắn thẻ & Đổi màu: {item?.name}</ModalTitle>
        </div>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-5">
          {/* Color palette */}
          <div>
            <label className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-ink">
              <Palette className="h-3.5 w-3.5" />
              Chọn màu nhận diện
            </label>
            <div className="flex flex-wrap gap-2">
              {PALETTE_COLORS.map((c) => (
                <button
                  key={c.name}
                  type="button"
                  onClick={() => setColor(c.value)}
                  className={`h-7 w-7 rounded-full border-2 transition-transform hover:scale-110 ${
                    color === c.value
                      ? "border-primary ring-2 ring-primary/30"
                      : "border-border"
                  }`}
                  style={{ backgroundColor: c.value || "#ffffff" }}
                  title={c.name}
                />
              ))}
            </div>
          </div>

          {/* Tags list */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-ink">
              Thẻ phân loại (Tags)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Nhập thẻ mới (vd: Quan trọng, Dự án A)..."
                value={inputTag}
                onChange={(e) => setInputTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag();
                  }
                }}
                className="apple-input flex-1 text-xs"
              />
              <Button variant="secondary" size="sm" onClick={addTag}>
                Thêm
              </Button>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-2">
              {tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-2.5 py-1 text-xs font-medium text-ink"
                >
                  #{t}
                  <button
                    type="button"
                    onClick={() => removeTag(t)}
                    className="hover:text-danger"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
              {tags.length === 0 && (
                <span className="text-xs text-ink-muted">Chưa có thẻ nào</span>
              )}
            </div>
          </div>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={processing} onClick={save}>
          {processing ? "Đang lưu..." : "Lưu thay đổi"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function StorageAnalyticsModal({
  open,
  close,
}: {
  open: boolean;
  close: () => void;
}) {
  const [data, setData] = useState<QuotaAnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError("");
    getStorageQuotaAnalyticsAPI()
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Không thể tải báo cáo")
      )
      .finally(() => setLoading(false));
  }, [open]);

  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <ModalTitle>Phân tích & Thống kê dung lượng</ModalTitle>
        </div>
      </ModalHeader>
      <ModalContent>
        {loading ? (
          <div className="py-12 text-center text-xs text-ink-muted">
            Đang tổng hợp dữ liệu dung lượng...
          </div>
        ) : error ? (
          <div className="rounded-lg bg-danger/10 p-3 text-xs text-danger">
            {error}
          </div>
        ) : data ? (
          <div className="space-y-6">
            {/* Overall storage bar */}
            <div className="space-y-2 rounded-2xl bg-surface-muted p-4">
              <div className="flex justify-between text-xs font-semibold text-ink">
                <span>Dung lượng đã sử dụng</span>
                <span>
                  {formatBytes(data.used_quota_bytes)} /{" "}
                  {formatBytes(data.total_quota_bytes)} ({data.usage_percentage}
                  %)
                </span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-border">
                <div
                  className={`h-full transition-all duration-500 ${
                    data.usage_percentage > 90
                      ? "bg-danger"
                      : data.usage_percentage > 75
                      ? "bg-amber-500"
                      : "bg-primary"
                  }`}
                  style={{ width: `${Math.min(100, data.usage_percentage)}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-ink-muted">
                <span>Còn trống: {formatBytes(data.free_quota_bytes)}</span>
                <span>
                  {data.total_files_count} tệp • {data.total_folders_count} thư
                  mục
                </span>
              </div>
            </div>

            {/* Category breakdown */}
            <div className="space-y-3">
              <p className="text-xs font-semibold text-ink">
                Phân bố theo thể loại
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {Object.entries(data.breakdown || {}).map(([key, info]) => {
                  const labels: Record<string, string> = {
                    documents: "Tài liệu văn bản",
                    images: "Hình ảnh",
                    videos: "Video",
                    audio: "Âm thanh",
                    archives: "Tệp nén / Lưu trữ",
                    code: "Mã nguồn & Code",
                    others: "Khác",
                  };
                  return (
                    <div
                      key={key}
                      className="flex items-center justify-between rounded-xl border border-border bg-surface p-3 text-xs"
                    >
                      <div className="space-y-0.5">
                        <span className="font-medium text-ink">
                          {labels[key] || key}
                        </span>
                        <p className="text-[11px] text-ink-muted">
                          {info.count} tệp • {info.percentage}%
                        </p>
                      </div>
                      <span className="font-semibold text-primary">
                        {formatBytes(info.size)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Trash summary */}
            <div className="flex items-center justify-between rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-xs">
              <div className="flex items-center gap-2">
                <Trash2 className="h-4 w-4 text-amber-500" />
                <span className="text-ink">Thùng rác đang chiếm:</span>
              </div>
              <span className="font-semibold text-ink">
                {data.trashed_files_count} tệp ({formatBytes(data.trashed_bytes)})
              </span>
            </div>
          </div>
        ) : null}
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Đóng
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function StorageActivitiesModal({
  item,
  close,
}: {
  item: StorageItem | null;
  close: () => void;
}) {
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!item) return;
    setLoading(true);
    getItemActivitiesAPI(item._id)
      .then(setActivities)
      .catch(() => setActivities([]))
      .finally(() => setLoading(false));
  }, [item]);

  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <ModalTitle>Nhật ký hoạt động: {item?.name}</ModalTitle>
        </div>
      </ModalHeader>
      <ModalContent>
        {loading ? (
          <div className="py-8 text-center text-xs text-ink-muted">
            Đang tải nhật ký...
          </div>
        ) : activities.length === 0 ? (
          <div className="py-8 text-center text-xs text-ink-muted">
            Chưa có ghi nhận hoạt động nào
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((act, i) => (
              <div
                key={act.id || i}
                className="flex items-start gap-3 rounded-xl border border-border bg-surface p-3 text-xs"
              >
                <div className="mt-0.5 rounded-full bg-primary/10 p-1 text-primary">
                  <Clock className="h-3.5 w-3.5" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-ink">
                      {act.action}
                    </span>
                    <span className="text-[11px] text-ink-muted">
                      {new Date(act.timestamp).toLocaleString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-[11px] text-ink-muted">
                    Thực hiện bởi: {act.user_id}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Đóng
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function StoragePreviewModal({
  item,
  previewUrl,
  close,
  downloadItem,
}: {
  item: StorageItem | null;
  previewUrl: string | null;
  close: () => void;
  downloadItem?: (item: StorageItem) => void;
}) {
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loadingText, setLoadingText] = useState(false);

  const ext = item?.name.split(".").pop()?.toLowerCase() || "";
  const mime = item?.mime_type || "";

  const isImage =
    mime.startsWith("image/") ||
    ["jpg", "jpeg", "png", "webp", "gif", "svg", "bmp"].includes(ext);
  const isPdf = mime === "application/pdf" || ext === "pdf";
  const isVideo =
    mime.startsWith("video/") || ["mp4", "webm", "ogg", "mov"].includes(ext);
  const isAudio =
    mime.startsWith("audio/") || ["mp3", "wav", "ogg", "m4a", "flac"].includes(ext);
  const isCodeOrText =
    mime.startsWith("text/") ||
    mime.includes("json") ||
    [
      "txt",
      "md",
      "json",
      "py",
      "js",
      "ts",
      "tsx",
      "jsx",
      "html",
      "css",
      "csv",
      "yaml",
      "yml",
      "sh",
      "sql",
    ].includes(ext);

  useEffect(() => {
    setZoom(100);
    setRotation(0);
    setTextContent(null);
    setCopied(false);

    if (item && isCodeOrText && previewUrl) {
      setLoadingText(true);
      fetch(previewUrl)
        .then((res) => res.text())
        .then((text) => setTextContent(text))
        .catch(() => setTextContent("Không thể tải nội dung xem trước"))
        .finally(() => setLoadingText(false));
    }
  }, [item, previewUrl, isCodeOrText]);

  const copyToClipboard = () => {
    if (!textContent) return;
    navigator.clipboard.writeText(textContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!item) return null;

  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <div className="flex w-full items-center justify-between gap-4">
          <div className="flex items-center gap-2 truncate">
            {isImage ? (
              <ImageIcon className="h-5 w-5 text-emerald-500 shrink-0" />
            ) : isPdf ? (
              <FileText className="h-5 w-5 text-rose-500 shrink-0" />
            ) : isVideo ? (
              <Film className="h-5 w-5 text-indigo-500 shrink-0" />
            ) : isAudio ? (
              <Music className="h-5 w-5 text-amber-500 shrink-0" />
            ) : isCodeOrText ? (
              <Code className="h-5 w-5 text-sky-500 shrink-0" />
            ) : (
              <FileText className="h-5 w-5 text-primary shrink-0" />
            )}
            <ModalTitle className="truncate">{item.name}</ModalTitle>
          </div>
          <div className="flex items-center gap-2">
            {previewUrl && (
              <a
                href={previewUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 rounded-lg border border-border px-2.5 py-1 text-xs font-medium text-ink hover:bg-surface-muted transition-colors"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Mở tab mới
              </a>
            )}
          </div>
        </div>
      </ModalHeader>

      <ModalContent className="max-h-[75vh] overflow-y-auto p-4">
        {!previewUrl ? (
          <div className="py-16 text-center text-xs text-ink-muted">
            Đang tạo liên kết xem trước trực tiếp...
          </div>
        ) : isImage ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2 rounded-xl bg-surface-muted p-2 text-xs">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom((z) => Math.max(25, z - 25))}
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span className="w-12 text-center font-medium">{zoom}%</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom((z) => Math.min(300, z + 25))}
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <div className="h-4 w-px bg-border mx-1" />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRotation((r) => (r + 90) % 360)}
              >
                <RotateCw className="h-4 w-4 mr-1" /> Xoay
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setZoom(100);
                  setRotation(0);
                }}
              >
                Đặt lại
              </Button>
            </div>
            <div className="flex min-h-[300px] items-center justify-center overflow-auto rounded-2xl bg-neutral-950/5 p-4 dark:bg-neutral-900">
              <img
                src={previewUrl}
                alt={item.name}
                className="max-h-[60vh] object-contain transition-transform duration-200"
                style={{
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                }}
              />
            </div>
          </div>
        ) : isPdf ? (
          <div className="space-y-2">
            <iframe
              src={`${previewUrl}#toolbar=1`}
              title={item.name}
              className="h-[65vh] w-full rounded-2xl border border-border bg-white shadow-sm"
            />
          </div>
        ) : isVideo ? (
          <div className="space-y-2">
            <video
              controls
              autoPlay={false}
              className="max-h-[65vh] w-full rounded-2xl bg-black shadow-lg"
              src={previewUrl}
            >
              Trình duyệt của bạn không hỗ trợ thẻ video HTML5.
            </video>
          </div>
        ) : isAudio ? (
          <div className="flex flex-col items-center justify-center space-y-6 rounded-2xl bg-surface-muted py-12 px-6">
            <div className="rounded-full bg-amber-500/10 p-6 text-amber-500 shadow-inner">
              <Music className="h-12 w-12" />
            </div>
            <div className="text-center">
              <h4 className="text-sm font-semibold text-ink">{item.name}</h4>
              <p className="text-xs text-ink-muted mt-1">{formatBytes(item.size)}</p>
            </div>
            <audio controls className="w-full max-w-md" src={previewUrl}>
              Trình duyệt của bạn không hỗ trợ thẻ audio HTML5.
            </audio>
          </div>
        ) : isCodeOrText ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-ink-muted">
              <span>Định dạng: {ext.toUpperCase() || "TEXT"}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={copyToClipboard}
                className="h-7 text-xs"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-500 mr-1" /> Đã sao chép
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5 mr-1" /> Sao chép mã
                  </>
                )}
              </Button>
            </div>
            {loadingText ? (
              <div className="py-12 text-center text-xs text-ink-muted">
                Đang tải văn bản...
              </div>
            ) : (
              <pre className="max-h-[55vh] overflow-auto rounded-2xl border border-border bg-neutral-950 p-4 text-xs font-mono text-neutral-200 shadow-inner">
                <code>{textContent}</code>
              </pre>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 rounded-2xl bg-surface-muted py-16 px-4 text-center">
            <div className="rounded-full bg-primary/10 p-5 text-primary">
              <FileText className="h-10 w-10" />
            </div>
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-ink">{item.name}</h4>
              <p className="text-xs text-ink-muted">
                Định dạng {ext.toUpperCase()} không hỗ trợ xem trước trực tuyến.
              </p>
              <p className="text-xs font-medium text-ink">
                Kích thước: {formatBytes(item.size)}
              </p>
            </div>
            {downloadItem && (
              <Button onClick={() => downloadItem(item)} className="gap-2">
                <Download className="h-4 w-4" /> Tải tệp xuống
              </Button>
            )}
          </div>
        )}
      </ModalContent>

      <ModalFooter>
        <div className="flex w-full items-center justify-between">
          <span className="text-xs text-ink-muted">{formatBytes(item.size)}</span>
          <div className="flex items-center gap-2">
            {downloadItem && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => downloadItem(item)}
                className="gap-1.5"
              >
                <Download className="h-3.5 w-3.5" /> Tải xuống
              </Button>
            )}
            <Button variant="secondary" size="sm" onClick={close}>
              Đóng
            </Button>
          </div>
        </div>
      </ModalFooter>
    </Modal>
  );
}


