"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import {
  File,
  Folder,
  RotateCcw,
  Share2,
  Star,
  Trash2,
  Upload,
} from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { StorageShareModal, StorageTextModal } from "./StorageModals";
import { StorageItem, StorageView, useStorage } from "./useStorage";

function size(value: number) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
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
  const [renameItem, setRenameItem] = useState<StorageItem | null>(null);
  const [shareItem, setShareItem] = useState<StorageItem | null>(null);
  const [versionItem, setVersionItem] = useState<StorageItem | null>(null);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    extension: "",
    min_size_mb: "",
    max_size_mb: "",
  });
  const tabs: { id: StorageView; label: string }[] = [
    { id: "files", label: "Tệp" },
    { id: "recent", label: "Gần đây" },
    { id: "starred", label: "Đã gắn sao" },
    { id: "trash", label: "Thùng rác" },
  ];
  return (
    <div className="w-full">
      <PageHeader
        title="Lưu trữ"
        actions={
          <>
            <input
              ref={input}
              type="file"
              multiple
              className="hidden"
              onChange={(event) =>
                event.target.files && state.upload(event.target.files)
              }
            />
            <Button variant="secondary" onClick={() => setFolderOpen(true)}>
              Tạo thư mục
            </Button>
            <Button
              icon={<Upload size={16} />}
              onClick={() => input.current?.click()}
            >
              Tải lên
            </Button>
          </>
        }
        meta={
          <nav className="flex flex-wrap gap-2">
            <button
              className="font-semibold text-ink"
              onClick={() => state.setPath([])}
            >
              Gốc
            </button>
            {state.path.map((folder, index) => (
              <span key={folder._id} className="flex gap-2">
                <span>/</span>
                <button
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
          { label: "Đã dùng", value: size(state.quota.used) },
          { label: "Giới hạn", value: size(state.quota.limit) },
          {
            label: "Còn lại",
            value: size(Math.max(0, state.quota.limit - state.quota.used)),
          },
        ]}
      />
      <div className="my-6 flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <SegmentedTabs<StorageView>
            label="Chế độ lưu trữ"
            value={state.view}
            onChange={(value) => {
              state.setPath([]);
              state.setView(value);
            }}
            tabs={tabs}
          />
        </div>
        <input
          value={state.query}
          onChange={(event) => state.setQuery(event.target.value)}
          className="apple-input sm:w-72"
          placeholder="Tìm tệp hoặc thư mục"
        />
        <Button
          variant="secondary"
          onClick={() => setAdvancedOpen((value) => !value)}
        >
          Lọc nâng cao
        </Button>
      </div>
      {advancedOpen && (
        <form
          className="mb-6 grid gap-3 rounded-panel border border-border bg-surface p-4 sm:grid-cols-[1fr_1fr_1fr_auto]"
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
            className="apple-input"
            placeholder="Phần mở rộng"
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
            className="apple-input"
            placeholder="Tối thiểu MB"
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
            className="apple-input"
            placeholder="Tối đa MB"
          />
          <Button type="submit">Áp dụng</Button>
        </form>
      )}
      {selectedIds.length > 0 && state.view !== "trash" && (
        <div className="mb-3 flex items-center justify-between border-y border-border py-3">
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
              Tải ZIP
            </Button>
          </div>
        </div>
      )}
      {state.loading ? (
        <PageLoader rows={7} />
      ) : state.items.length ? (
        <ul className="overflow-hidden rounded-panel border border-border bg-surface">
          {state.items.map((item) => (
            <li
              key={item._id}
              className="flex flex-col gap-4 border-b border-border px-5 py-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
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
                          : rows.filter((id) => id !== item._id),
                      )
                    }
                    className="h-4 w-4 accent-[hsl(var(--brand))]"
                  />
                )}
                {item.is_folder ? (
                  <Folder size={18} className="shrink-0 text-brand" />
                ) : (
                  <File size={18} className="shrink-0 text-ink-muted" />
                )}
                {item.is_folder ? (
                  <button
                    onClick={() => state.setPath([...state.path, item])}
                    className="min-w-0 truncate text-left text-[14px] font-semibold text-ink hover:text-brand"
                  >
                    {item.name}
                  </button>
                ) : (
                  <div className="min-w-0">
                    <Link
                      href={`/tai-lieu/xem-truoc/${item._id}?url=${encodeURIComponent(item.url || "")}&name=${encodeURIComponent(item.name)}`}
                      className="block truncate text-[14px] font-semibold text-ink hover:text-brand"
                    >
                      {item.name}
                    </Link>
                    <p className="mt-1 text-[12px] text-ink-muted">
                      {size(item.size)} ·{" "}
                      {new Date(
                        item.updated_at || item.created_at,
                      ).toLocaleDateString("vi-VN")}
                    </p>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1">
                {state.view === "trash" ? (
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label="Khôi phục"
                    onClick={() => state.restore(item)}
                  >
                    <RotateCcw size={16} />
                  </Button>
                ) : (
                  <>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Đánh dấu sao"
                      onClick={() => state.toggleStar(item)}
                    >
                      <Star
                        size={16}
                        fill={item.is_starred ? "currentColor" : "none"}
                      />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Chia sẻ"
                      onClick={() => setShareItem(item)}
                    >
                      <Share2 size={16} />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setRenameItem(item)}
                    >
                      Đổi tên
                    </Button>
                    {!item.is_folder && (
                      <>
                        <input
                          ref={versionInput}
                          type="file"
                          className="hidden"
                          onChange={(event) => {
                            const file = event.target.files?.[0];
                            if (versionItem && file)
                              state.uploadVersion(versionItem, file);
                          }}
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setVersionItem(item);
                            requestAnimationFrame(() =>
                              versionInput.current?.click(),
                            );
                          }}
                        >
                          Bản mới
                        </Button>
                      </>
                    )}
                  </>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Xóa"
                  onClick={() => state.remove(item)}
                >
                  <Trash2 size={16} />
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
              ? "Thùng rác đang trống"
              : "Tải lên tệp hoặc tạo thư mục để bắt đầu"
          }
        />
      )}
      <StorageTextModal
        open={folderOpen}
        close={() => setFolderOpen(false)}
        title="Tạo thư mục"
        label="Tên thư mục"
        processing={state.processing === "folder"}
        submit={state.createFolder}
      />
      <StorageTextModal
        open={Boolean(renameItem)}
        close={() => setRenameItem(null)}
        title="Đổi tên"
        label="Tên mới"
        processing={state.processing === "rename"}
        submit={(value) => state.rename(renameItem!, value)}
      />
      <StorageShareModal
        item={shareItem}
        close={() => setShareItem(null)}
        processing={state.processing === "share"}
        submit={(email, role) => state.share(shareItem!, email, role)}
        createLink={(password, expiresInHours) =>
          state.createProtectedLink(shareItem!, password, expiresInHours)
        }
      />
    </div>
  );
}
