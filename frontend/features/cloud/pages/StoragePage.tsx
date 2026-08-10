"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  Download,
  Eye,
  File,
  Folder,
  Lock,
  MoreHorizontal,
  Star,
  Trash2,
  Upload,
  UploadCloud,
} from "lucide-react";
import InlineState from "@/shared/components/common/InlineState";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import {
  StorageActivitiesModal,
  StorageAnalyticsModal,
  StoragePreviewModal,
  StorageShareModal,
  StorageTagColorModal,
  StorageTextModal,
  StorageVersionModal,
} from "../components/StorageModals";
import { StorageItem, StorageView, useStorage } from "../hooks/useStorage";

function size(value: number) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1,
  );
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

export default function StoragePage() {
  const state = useStorage();
  useNoticeToast(state.notice);
  useNoticeToast(state.error, "error");
  const input = useRef<HTMLInputElement>(null);
  const versionInput = useRef<HTMLInputElement>(null);

  const [folderOpen, setFolderOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [renameItem, setRenameItem] = useState<StorageItem | null>(null);
  const [shareItem, setShareItem] = useState<StorageItem | null>(null);
  const [versionItem, setVersionItem] = useState<StorageItem | null>(null);
  const [tagColorItem, setTagColorItem] = useState<StorageItem | null>(null);
  const [activityItem, setActivityItem] = useState<StorageItem | null>(null);
  const [targetUploadVersionItem, setTargetUploadVersionItem] =
    useState<StorageItem | null>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    item: StorageItem;
  } | null>(null);

  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    extension: "",
    min_size_mb: "",
    max_size_mb: "",
  });

  const tabs: { id: StorageView; label: string }[] = [
    { id: "files", label: "Tất cả tệp" },
    { id: "recent", label: "Gần đây" },
    { id: "starred", label: "Yêu thích" },
    { id: "shared", label: "Được chia sẻ" },
    { id: "trash", label: "Thùng rác" },
  ];

  const allTags = Array.from(
    new Set(state.items.flatMap((item) => item.tags || []))
  );

  useEffect(() => {
    const handleOutside = () => setContextMenu(null);
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setContextMenu(null);
    };
    window.addEventListener("click", handleOutside);
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("click", handleOutside);
      window.removeEventListener("keydown", handleKey);
    };
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      state.upload(e.dataTransfer.files);
    }
  };

  const handleContextMenu = (e: React.MouseEvent, item: StorageItem) => {
    e.preventDefault();
    e.stopPropagation();
    const x = Math.min(e.clientX, window.innerWidth - 220);
    const y = Math.min(e.clientY, window.innerHeight - 340);
    setContextMenu({ x, y, item });
  };

  const downloadItem = (item: StorageItem) => {
    if (item.url) {
      const link = document.createElement("a");
      link.href = item.url;
      link.download = item.name;
      link.target = "_blank";
      link.click();
    } else {
      state.openPreview(item);
    }
  };

  return (
    <div
      className="relative w-full min-h-[85vh]"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {isDragging && (
        <div className="pointer-events-none fixed inset-0 z-50 flex flex-col items-center justify-center bg-primary/15 backdrop-blur-md transition-all duration-300">
          <div className="flex flex-col items-center gap-4 rounded-3xl border-2 border-dashed border-primary bg-surface/90 p-10 shadow-2xl animate-bounce">
            <div className="rounded-full bg-brand-soft p-5 text-brand">
              <UploadCloud className="h-14 w-14" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-bold text-ink">
                Thả tệp vào đây để tải lên
              </h3>
            </div>
          </div>
        </div>
      )}

      {state.uploadProgress !== null && (
        <div className="mb-4 overflow-hidden rounded-2xl border border-primary/30 bg-primary/5 p-4 shadow-sm backdrop-blur-md">
          <div className="flex items-center justify-between text-xs font-semibold text-primary">
            <div className="flex items-center gap-2">
              <UploadCloud className="h-4 w-4 animate-pulse" />
              <span>Đang tải tệp lên</span>
            </div>
            <span>{state.uploadProgress}%</span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-primary/20">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${state.uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      <PageHeader
        title="Lưu trữ"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={input}
              type="file"
              multiple
              className="hidden"
              onChange={(event) =>
                event.target.files && state.upload(event.target.files)
              }
            />
            <input
              ref={versionInput}
              type="file"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file && targetUploadVersionItem) {
                  state.uploadVersion(targetUploadVersionItem, file);
                  setTargetUploadVersionItem(null);
                }
              }}
            />

            <Button
              variant="secondary"
              onClick={() => setAnalyticsOpen(true)}
            >
              Phân tích
            </Button>
            <Button
              variant="secondary"
              onClick={() => setFolderOpen(true)}
            >
              Thư mục mới
            </Button>
            <Button
              onClick={() => input.current?.click()}
              disabled={state.processing === "upload"}
            >
              {state.processing === "upload" ? "Đang tải lên" : "Tải tệp lên"}
            </Button>
          </div>
        }
      />
      <MetricStrip
        items={[
          { label: "Đã sử dụng", value: size(state.quota.used) },
          { label: "Giới hạn gói", value: size(state.quota.limit) },
          {
            label: "Dung lượng trống",
            value: size(Math.max(0, state.quota.limit - state.quota.used)),
          },
        ]}
      />
      <div className="my-6 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <SegmentedTabs<StorageView>
            label="Chế độ lưu trữ"
            value={state.view}
            onChange={(value) => {
              state.setPath([]);
              state.setSelectedTag("");
              state.setView(value);
            }}
            tabs={tabs}
          />
        </div>
        <Button
          variant="secondary"
          onClick={() => setAdvancedOpen((value) => !value)}
        >
          Lọc nâng cao
        </Button>
      </div>

      {state.path.length > 0 && state.view === "files" && (
        <div className="mb-4 flex items-center gap-2 rounded-panel bg-surface-quiet px-4 py-2 text-xs font-medium text-ink">
          <button
            type="button"
            onClick={() => state.setPath([])}
            className="text-brand hover:underline"
          >
            Gốc
          </button>
          {state.path.map((folder, idx) => (
            <span key={folder._id} className="flex items-center gap-2">
              <span className="text-ink-muted">/</span>
              {idx === state.path.length - 1 ? (
                <span className="font-semibold text-ink">{folder.name}</span>
              ) : (
                <button
                  type="button"
                  onClick={() => state.setPath(state.path.slice(0, idx + 1))}
                  className="text-brand hover:underline"
                >
                  {folder.name}
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {allTags.length > 0 && state.view === "files" && (
        <div className="mb-4 flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold text-ink-muted">
            Lọc theo thẻ:
          </span>
          <button
            type="button"
            onClick={() => state.setSelectedTag("")}
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
              !state.selectedTag
                ? "bg-primary text-white"
                : "bg-surface-muted text-ink hover:bg-border"
            }`}
          >
            Tất cả
          </button>
          {allTags.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() =>
                state.setSelectedTag(state.selectedTag === t ? "" : t)
              }
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                state.selectedTag === t
                  ? "bg-primary text-white"
                  : "bg-surface-muted text-ink hover:bg-border"
              }`}
            >
              #{t}
            </button>
          ))}
        </div>
      )}
      {advancedOpen && (
        <form
          className="mb-6 grid gap-3 rounded-2xl border border-border bg-surface p-4 sm:grid-cols-[1fr_1fr_1fr_auto]"
          onSubmit={async (event) => {
            event.preventDefault();
            await state.advancedSearch({
              q: state.query.trim() || undefined,
              extension: filters.extension.trim() || undefined,
              min_size_mb: filters.min_size_mb
                ? Number(filters.min_size_mb)
                : undefined,
              max_size_mb: filters.max_size_mb
                ? Number(filters.max_size_mb)
                : undefined,
            });
          }}
        >
          <input
            value={filters.extension}
            onChange={(event) =>
              setFilters((value) => ({
                ...value,
                extension: event.target.value,
              }))
            }
            className="apple-input text-xs"
            placeholder="Đuôi tệp như pdf hoặc png"
          />
          <input
            type="number"
            min="0"
            value={filters.min_size_mb}
            onChange={(event) =>
              setFilters((value) => ({
                ...value,
                min_size_mb: event.target.value,
              }))
            }
            className="apple-input text-xs"
            placeholder="Dung lượng tối thiểu (MB)"
          />
          <input
            type="number"
            min="0"
            value={filters.max_size_mb}
            onChange={(event) =>
              setFilters((value) => ({
                ...value,
                max_size_mb: event.target.value,
              }))
            }
            className="apple-input text-xs"
            placeholder="Dung lượng tối đa (MB)"
          />
          <Button type="submit">Áp dụng lọc</Button>
        </form>
      )}

      {state.view === "trash" && state.items.length > 0 && (
        <div className="mb-3 flex items-center justify-between rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-2.5">
          <p className="text-[13px] font-semibold text-ink">
            Thùng rác ({state.items.length} mục)
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => state.autoPurgeTrash(30)}
              disabled={state.processing === "autoPurge"}
              title="Tự động xóa vĩnh viễn các mục rác tồn tại trên 30 ngày"
              className="text-xs"
            >
              Tự động dọn rác 30 ngày
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={() => state.emptyTrash()}
              disabled={state.processing === "emptyTrash"}
              className="text-xs"
            >
              Dọn sạch toàn bộ
            </Button>
          </div>
        </div>
      )}

      {selectedIds.length > 0 && state.view !== "trash" && (
        <div className="mb-3 flex items-center justify-between rounded-xl border border-border bg-surface-muted px-4 py-2.5">
          <p className="text-[13px] font-semibold text-ink">
            Đã chọn {selectedIds.length} mục
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedIds([])}
            >
              Bỏ chọn
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={state.processing === "download"}
              onClick={() => state.downloadSelected(selectedIds)}
            >
              Tải xuống ZIP
            </Button>
          </div>
        </div>
      )}
      {state.loading ? (
        <PageLoader rows={7} />
      ) : state.items.length ? (
        <ul className="overflow-hidden rounded-2xl border border-border bg-surface shadow-xs">
          {state.items.map((item) => (
            <li
              key={item._id}
              onContextMenu={(e) => handleContextMenu(e, item)}
              className="flex flex-col gap-3 border-b border-border px-5 py-3.5 last:border-b-0 transition-colors hover:bg-surface-muted/40 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex min-w-0 items-center gap-3">
                {state.view !== "trash" && (
                  <input
                    type="checkbox"
                    aria-label={`Chọn ${item.name}`}
                    checked={selectedIds.includes(item._id)}
                    onChange={(event) =>
                      setSelectedIds((rows) =>
                        event.target.checked
                          ? [...rows, item._id]
                          : rows.filter((id) => id !== item._id)
                      )
                    }
                    className="h-4 w-4 rounded accent-primary"
                  />
                )}
                {state.view !== "trash" && (
                  <button
                    type="button"
                    onClick={() => state.toggleStar(item)}
                    className="text-ink-muted hover:text-amber-500 transition-colors"
                    title={item.is_starred ? "Gỡ yêu thích" : "Yêu thích"}
                  >
                    <Star
                      className={`h-4 w-4 ${
                        item.is_starred
                          ? "fill-amber-400 text-amber-500"
                          : "text-ink-muted/60"
                      }`}
                    />
                  </button>
                )}
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                  style={{
                    backgroundColor: item.color
                      ? `${item.color}20`
                      : "transparent",
                  }}
                >
                  {item.is_folder ? (
                    <Folder
                      size={20}
                      style={{ color: item.color || "var(--brand, #3B82F6)" }}
                    />
                  ) : (
                    <File
                      size={20}
                      style={{ color: item.color || "currentColor" }}
                      className={!item.color ? "text-ink-muted" : ""}
                    />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {item.is_folder ? (
                      <button
                        onClick={() => state.setPath([...state.path, item])}
                        className="truncate text-left text-[14px] font-semibold text-ink hover:text-primary transition-colors"
                      >
                        {item.name}
                      </button>
                    ) : (
                      <button
                        onClick={() => state.openPreview(item)}
                        className="truncate text-left text-[14px] font-semibold text-ink hover:text-primary transition-colors"
                      >
                        {item.name}
                      </button>
                    )}
                    {item.is_locked && (
                      <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600">
                        <Lock className="h-3 w-3" />
                        Đang khóa
                      </span>
                    )}
                    {item.tags?.map((t) => (
                      <span
                        key={t}
                        className="rounded-full bg-surface-muted border border-border px-2 py-0.2 text-[10px] font-medium text-ink-muted"
                      >
                        #{t}
                      </span>
                    ))}
                  </div>
                  <p className="mt-0.5 flex items-center gap-2 text-[12px] text-ink-muted">
                    <span>{size(item.size)}</span>
                    <span>•</span>
                    <span>
                      {new Date(
                        item.updated_at || item.created_at
                      ).toLocaleDateString("vi-VN")}
                    </span>
                    {item.versions && item.versions.length > 0 && (
                      <>
                        <span>•</span>
                        <span className="text-primary font-medium">
                          {item.versions.length + 1} phiên bản
                        </span>
                      </>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-1">
                {state.view === "trash" ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => state.restore(item)}
                    className="text-xs text-primary hover:bg-primary/10"
                  >
                    Khôi phục
                  </Button>
                ) : (
                  <>
                    {!item.is_folder && (
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label="Xem trước"
                        onClick={() => state.openPreview(item)}
                        title="Xem trước trực tuyến (PDF, Ảnh, Video, Code)"
                      >
                        <Eye size={15} />
                      </Button>
                    )}
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Thêm thao tác cho ${item.name}`}
                      title="Thêm thao tác"
                      onClick={(event) => {
                        event.stopPropagation();
                        const rect = event.currentTarget.getBoundingClientRect();
                        setContextMenu({
                          x: Math.max(12, rect.right - 224),
                          y: Math.min(window.innerHeight - 420, rect.bottom + 6),
                          item,
                        });
                      }}
                    >
                      <MoreHorizontal size={16} />
                    </Button>
                  </>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Xóa"
                  onClick={() => state.remove(item)}
                  className="text-ink-muted hover:text-danger hover:bg-danger/10"
                  title={
                    state.view === "trash"
                      ? "Xóa vĩnh viễn"
                      : "Chuyển vào thùng rác"
                  }
                >
                  <Trash2 size={15} />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <InlineState
          title={
            state.view === "trash"
              ? "Thùng rác đang trống"
              : state.view === "starred"
                ? "Chưa có mục yêu thích"
                : state.view === "shared"
                  ? "Chưa có mục được chia sẻ"
                  : "Chưa có tệp"
          }
        />
      )}

      {contextMenu && (
        <div
          className="fixed z-50 min-w-[200px] rounded-2xl border border-border bg-surface/95 p-1.5 shadow-2xl backdrop-blur-xl animate-in fade-in zoom-in-95"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-2 py-1.5 text-[11px] font-semibold text-ink-muted truncate border-b border-border/60 mb-1">
            {contextMenu.item.name}
          </div>
          {!contextMenu.item.is_folder && (
            <button
              onClick={() => {
                state.openPreview(contextMenu.item);
                setContextMenu(null);
              }}
              className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
            >
              Xem trước
            </button>
          )}
          {contextMenu.item.is_folder && (
            <button
              onClick={() => {
                state.setPath([...state.path, contextMenu.item]);
                setContextMenu(null);
              }}
              className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
            >
              Mở thư mục
            </button>
          )}
          <button
            onClick={() => {
              state.toggleStar(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
          >
            {contextMenu.item.is_starred ? "Gỡ dấu sao" : "Gắn dấu sao"}
          </button>
          <button
            onClick={() => {
              setShareItem(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
          >
            Chia sẻ
          </button>
          <button
            onClick={() => {
              setTagColorItem(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
          >
            Nhãn và màu
          </button>
          {!contextMenu.item.is_folder && (
            <>
              <button
                onClick={() => {
                  setVersionItem(contextMenu.item);
                  setContextMenu(null);
                }}
                className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
              >
                Lịch sử phiên bản
              </button>
              <button
                onClick={() => {
                  contextMenu.item.is_locked
                    ? state.unlock(contextMenu.item)
                    : state.lock(contextMenu.item);
                  setContextMenu(null);
                }}
                className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
              >
                {contextMenu.item.is_locked ? "Mở khóa tệp" : "Khóa tệp"}
              </button>
            </>
          )}
          <button
            onClick={() => {
              setActivityItem(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
          >
            Nhật ký hoạt động
          </button>
          <button
            onClick={() => {
              setRenameItem(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
          >
            Đổi tên
          </button>
          {!contextMenu.item.is_folder && (
            <button
              onClick={() => {
                downloadItem(contextMenu.item);
                setContextMenu(null);
              }}
              className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-ink hover:bg-surface-quiet transition-colors"
            >
              Tải xuống
            </button>
          )}
          <div className="h-px bg-border my-1" />
          <button
            onClick={() => {
              state.remove(contextMenu.item);
              setContextMenu(null);
            }}
            className="flex w-full items-center rounded-control px-2.5 py-2 text-xs font-medium text-danger hover:bg-danger-soft transition-colors"
          >
            {state.view === "trash" ? "Xóa vĩnh viễn" : "Chuyển vào thùng rác"}
          </button>
        </div>
      )}

      <StoragePreviewModal
        item={state.previewItem}
        previewUrl={state.previewUrl}
        close={state.closePreview}
        downloadItem={downloadItem}
      />
      <StorageTextModal
        open={folderOpen}
        close={() => setFolderOpen(false)}
        title="Tạo thư mục mới"
        label="Tên thư mục"
        processing={state.processing === "folder"}
        submit={state.createFolder}
      />
      <StorageTextModal
        open={Boolean(renameItem)}
        close={() => setRenameItem(null)}
        title="Đổi tên"
        label="Tên mới"
        initialValue={renameItem?.name || ""}
        processing={state.processing === "rename"}
        submit={(value) => state.rename(renameItem!, value)}
      />
      <StorageShareModal
        item={shareItem}
        close={() => setShareItem(null)}
        processing={
          state.processing === "share" || state.processing === "revokeShare"
        }
        submit={(email, role) => state.share(shareItem!, email, role)}
        revokeShare={(targetUserId) =>
          state.revokeShare(shareItem!, targetUserId)
        }
        createLink={(password, expiresInHours) =>
          state.createProtectedLink(shareItem!, password, expiresInHours)
        }
      />
      <StorageVersionModal
        item={versionItem}
        close={() => setVersionItem(null)}
        processing={state.processing === "rollback"}
        onRollback={(versionId) =>
          state.rollbackVersion(versionItem!, versionId)
        }
        onUploadNew={() => {
          if (versionItem) {
            setTargetUploadVersionItem(versionItem);
            requestAnimationFrame(() => versionInput.current?.click());
          }
        }}
      />
      <StorageTagColorModal
        item={tagColorItem}
        close={() => setTagColorItem(null)}
        processing={state.processing === "tagColor"}
        onSave={(tags, color) =>
          state.updateTagAndColor(tagColorItem!, tags, color)
        }
      />
      <StorageAnalyticsModal
        open={analyticsOpen}
        close={() => setAnalyticsOpen(false)}
      />
      <StorageActivitiesModal
        item={activityItem}
        close={() => setActivityItem(null)}
      />
    </div>
  );
}
