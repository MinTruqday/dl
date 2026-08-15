"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Bookmark, Minus, Plus } from "lucide-react";
import InlineState from "@/shared/components/common/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import ReaderPanel from "../components/ReaderPanel";
import { useDocumentReader } from "../hooks/useDocumentReader";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";

export default function DocumentReaderPage() {
  const { id } = useParams<{ id: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const reader = useDocumentReader(
    id,
    search.get("url"),
    search.get("name"),
    search.get("pwd"),
  );
  useNoticeToast(reader.notice);
  const [password, setPassword] = useState("");
  const [zoom, setZoom] = useState(100);
  if (reader.loading) return <PageLoader rows={8} />;
  if (reader.locked)
    return (
      <div className="mx-auto max-w-md py-16">
        <InlineState
          title="Tài liệu được bảo vệ"
          detail="Nhập mật khẩu để tiếp tục"
        />
        <div className="mt-4 flex gap-2">
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="apple-input min-w-0 flex-1"
          />
          <Button disabled={!password} onClick={() => reader.load(password)}>
            Mở tài liệu
          </Button>
        </div>
      </div>
    );
  if (!reader.document)
    return (
      <InlineState
        title="Không thể mở tài liệu"
        detail={reader.error || "Tài liệu không tồn tại"}
        tone="danger"
        action={
          <Button variant="secondary" onClick={() => router.back()}>
            Quay lại
          </Button>
        }
      />
    );
  const document = reader.document;
  const fileView =
    document.content_format === "raw" ||
    (document.file_url &&
      ["pdf", "html"].includes(String(document.content_format).toLowerCase()));
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-surface">
      <header className="flex h-[60px] shrink-0 items-center justify-between gap-4 border-b border-border bg-surface px-4">
        <div className="flex min-w-0 items-center gap-3">
          <Button size="sm" variant="ghost" onClick={() => router.back()}>
            Quay lại
          </Button>
          <p className="truncate text-[14px] font-semibold text-ink">
            {document.title || "Tài liệu"}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            aria-label="Thu nhỏ"
            onClick={() => setZoom((value) => Math.max(60, value - 10))}
          >
            <Minus size={16} />
          </Button>
          <span className="w-14 text-center text-[12px] text-ink-muted">
            {zoom}%
          </span>
          <Button
            size="icon"
            variant="ghost"
            aria-label="Phóng to"
            onClick={() => setZoom((value) => Math.min(180, value + 10))}
          >
            <Plus size={16} />
          </Button>
          <Button
            size="icon"
            variant={reader.bookmarked ? "primary" : "ghost"}
            aria-label="Lưu tài liệu"
            onClick={reader.bookmark}
          >
            <Bookmark
              size={16}
              fill={reader.bookmarked ? "currentColor" : "none"}
            />
          </Button>
        </div>
      </header>
      {reader.error && (
        <div className="border-b border-border p-3">
          <InlineState
            title="Không thể hoàn tất thao tác"
            detail={reader.error}
            tone="danger"
          />
        </div>
      )}
      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 overflow-auto bg-surface-quiet p-4 md:p-8">
          {document.content_format === "zip" ? (
            <div className="mx-auto min-h-full max-w-4xl rounded-workspace border border-border bg-surface p-6">
              <h1 className="mb-5 text-[18px] font-semibold text-ink">
                {reader.archiveFile?.name || "Chọn tệp từ bảng công cụ"}
              </h1>
              <pre className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-ink">
                {reader.processing === "archive"
                  ? "Đang tải"
                  : reader.archiveFile?.content || ""}
              </pre>
            </div>
          ) : fileView ? (
            <iframe
              title={document.title}
              src={document.file_url}
              className="h-full min-h-[720px] w-full rounded-workspace border border-border bg-surface"
            />
          ) : (
            <article
              className="mx-auto min-h-full max-w-3xl origin-top rounded-workspace border border-border bg-surface px-7 py-10 md:px-14"
              style={{ transform: `scale(${zoom / 100})` }}
            >
              <h1 className="mb-8 text-[26px] font-semibold tracking-[-0.02em] text-ink">
                {document.title}
              </h1>
              <div className="whitespace-pre-wrap text-[16px] leading-8 text-ink">
                {reader.content || "Tài liệu chưa có nội dung"}
              </div>
            </article>
          )}
        </main>
        <ReaderPanel reader={reader} />
      </div>
    </div>
  );
}
