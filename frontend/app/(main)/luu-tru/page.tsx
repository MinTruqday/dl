"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import {
  BarChart3,
  Clock,
  File,
  Folder,
  History,
  Lock,
  Palette,
  RotateCcw,
  Share2,
  Star,
  Trash2,
  Unlock,
  Upload,
} from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  StorageActivitiesModal,
  StorageAnalyticsModal,
  StorageShareModal,
  StorageTagColorModal,
  StorageTextModal,
  StorageVersionModal,
} from "./StorageModals";
import { StorageItem, StorageView, useStorage } from "./useStorage";

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

  return (
    <div className="w-full">
      <PageHeader
        title="Lưu trữ đám mây"
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
                if (targetUploadVersionItem && file) {
                  state.uploadVersion(targetUploadVersionItem, file);
                }
              }}
            />

            <Button
              variant="secondary"
              onClick={() => setAnalyticsOpen(true)}
            >
              <BarChart3 className="mr-1.5 h-4 w-4" />
              Thống kê dung lượng
            </Button>

            {state.view === "trash" ? (
              <Button
                variant="secondary"
                disabled={
                  state.items.length === 0 || state.processing === "emptyTrash"
                }
                onClick={() => {
                  if (
                    confirm(
                      "Bạn có chắc chắn muốn dọn sạch toàn bộ thùng rác? Thao tác này không thể hoàn tác!"
                    )
                  ) {
                    state.emptyTrash();
                  }
                }}
              >
                <Trash2 className="mr-1.5 h-4 w-4 text-danger" />
                Dọn sạch thùng rác
              </Button>
            ) : (
              <>
                <Button
                  variant="secondary"
                  onClick={() => setFolderOpen(true)}
                >
                  Tạo thư mục
                </Button>
                <Button
                  onClick={() => input.current?.click()}
                >
                  <Upload className="mr-1.5 h-4 w-4" />
                  Tải lên
                </Button>
              </>
            )}
          </div>
        }
        meta={
          <nav className="flex flex-wrap items-center gap-2 text-xs">
            <button
              className={`font-semibold transition-colors ${
                state.path.length === 0 ? "text-primary" : "text-ink hover:text-primary"
              }`}
              onClick={() => state.setPath([])}
            >
              Thư mục gốc
            </button>
            {state.path.map((folder, index) => (
              <span key={folder._id} className="flex items-center gap-2">
                <span className="text-ink-muted">/</span>
                <button
                  className={`font-medium transition-colors ${
                    index === state.path.length - 1
                      ? "text-primary font-semibold"
                      : "text-ink hover:text-primary"
                  }`}
                  onClick={() => state.setPath(state.path.slice(0, index + 1))}
                >
                  {folder.name}
                </button>
              </span>
            ))}
          </nav>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể xử lý kho lưu trữ"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {state.notice && (
        <div className="mb-6">
          <InlineState
            title={state.notice}
            action={
              <Button variant="ghost" onClick={state.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}
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
      <div className="my-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex-1">
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
        <input
          value={state.query}
          onChange={(event) => state.setQuery(event.target.value)}
          className="apple-input sm:w-72"
          placeholder="Tìm kiếm tệp hoặc thư mục..."
        />
        <Button
          variant="secondary"
          onClick={() => setAdvancedOpen((value) => !value)}
        >
          Lọc nâng cao
        </Button>
      </div>
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
            placeholder="Đuôi tệp (.pdf, .png...)"
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
                      <Link
                        href={`/tai-lieu/xem-truoc/${item._id}?url=${encodeURIComponent(
                          item.url || ""
                        )}&name=${encodeURIComponent(item.name)}`}
                        className="truncate text-[14px] font-semibold text-ink hover:text-primary transition-colors"
                      >
                        {item.name}
                      </Link>
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
                    <RotateCcw className="mr-1 h-3.5 w-3.5" />
                    Khôi phục
                  </Button>
                ) : (
                  <>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Chia sẻ"
                      onClick={() => setShareItem(item)}
                      title="Chia sẻ nội bộ & tạo liên kết"
                    >
                      <Share2 size={15} />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Gắn thẻ & đổi màu"
                      onClick={() => setTagColorItem(item)}
                      title="Gắn thẻ & đổi màu nhận diện"
                    >
                      <Palette size={15} />
                    </Button>
                    {!item.is_folder && (
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label="Lịch sử phiên bản"
                        onClick={() => setVersionItem(item)}
                        title="Lịch sử phiên bản & Rollback"
                      >
                        <History size={15} />
                      </Button>
                    )}
                    {!item.is_folder && (
                      <Button
                        size="icon"
                        variant="ghost"
                        aria-label={item.is_locked ? "Mở khóa" : "Khóa tệp"}
                        onClick={() =>
                          item.is_locked ? state.unlock(item) : state.lock(item)
                        }
                        title={
                          item.is_locked ? "Mở khóa tệp" : "Khóa tệp (tránh sửa)"
                        }
                      >
                        {item.is_locked ? (
                          <Unlock size={15} className="text-amber-500" />
                        ) : (
                          <Lock size={15} />
                        )}
                      </Button>
                    )}
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Nhật ký hoạt động"
                      onClick={() => setActivityItem(item)}
                      title="Nhật ký hoạt động"
                    >
                      <Clock size={15} />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setRenameItem(item)}
                      className="text-xs"
                    >
                      Đổi tên
                    </Button>
                  </>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Xóa"
                  onClick={() => state.remove(item)}
                  className="text-ink-muted hover:text-danger hover:bg-danger/10"
                  title={state.view === "trash" ? "Xóa vĩnh viễn" : "Chuyển vào thùng rác"}
                >
                  <Trash2 size={15} />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <InlineState
          title="Không có dữ liệu"
          detail={
            state.view === "trash"
              ? "Thùng rác đang trống."
              : state.view === "starred"
              ? "Bạn chưa gắn sao mục nào."
              : state.view === "shared"
              ? "Chưa có tệp nào được chia sẻ với bạn."
              : "Tải lên tệp hoặc tạo thư mục để bắt đầu."
          }
        />
      )}
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
        processing={state.processing === "share" || state.processing === "revokeShare"}
        submit={(email, role) => state.share(shareItem!, email, role)}
        revokeShare={(targetUserId) => state.revokeShare(shareItem!, targetUserId)}
        createLink={(password, expiresInHours) =>
          state.createProtectedLink(shareItem!, password, expiresInHours)
        }
      />
      <StorageVersionModal
        item={versionItem}
        close={() => setVersionItem(null)}
        processing={state.processing === "rollback"}
        onRollback={(versionId) => state.rollbackVersion(versionItem!, versionId)}
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
        onSave={(tags, color) => state.updateTagAndColor(tagColorItem!, tags, color)}
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
