"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Bookmark, Share2 } from "lucide-react";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import DocumentDiscussion from "../components/DocumentDiscussion";
import { useDocumentDetails } from "../hooks/useDocumentDetails";

type Tab = "content" | "chapters" | "discussion";
export default function DocumentDetailsPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const state = useDocumentDetails(slug);
  useNoticeToast(state.notice);
  const [tab, setTab] = useState<Tab>("content");
  if (state.loading) return <PageLoader rows={6} />;
  if (!state.document)
    return (
      <InlineState
        title="Không thể mở tài liệu"
        detail={state.error || "Tài liệu không tồn tại"}
        tone="danger"
        action={
          <Button variant="secondary" onClick={() => router.back()}>
            Quay lại
          </Button>
        }
      />
    );
  const document = state.document;
  const id = document._id ?? document.id;
  return (
    <div className="w-full">
      <PageHeader
        title={document.title}
        showTitle
        description={document.description}
        actions={
          <>
            <Button
              size="icon"
              variant="secondary"
              aria-label="Chia sẻ"
              onClick={state.share}
            >
              <Share2 size={17} />
            </Button>
            <Button
              variant={state.pinned ? "primary" : "secondary"}
              disabled={state.processing}
              onClick={state.pin}
            >
              {state.pinned ? "Bỏ ghim" : "Ghim"}
            </Button>
            <Button
              size="icon"
              variant={state.bookmarked ? "primary" : "secondary"}
              aria-label="Lưu tài liệu"
              disabled={state.processing}
              onClick={state.bookmark}
            >
              <Bookmark
                size={17}
                fill={state.bookmarked ? "currentColor" : "none"}
              />
            </Button>
            <Button onClick={() => router.push(`/tai-lieu/xem-truoc/${id}`)}>
              Đọc tài liệu
            </Button>
          </>
        }
        meta={
          <div className="flex flex-wrap gap-x-5 gap-y-2">
            <span>
              {document.author?.full_name ||
                document.author_name ||
                "Tác giả chưa xác định"}
            </span>
            <span>
              {document.category_name || document.category || "Chưa phân loại"}
            </span>
            <span>
              {Number(
                document.views_count ?? document.views ?? 0,
              ).toLocaleString("vi-VN")}{" "}
              lượt xem
            </span>
          </div>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể hoàn tất thao tác"
            detail={state.error}
            tone="danger"
          />
        </div>
      )}
      <div className="mb-6">
        <SegmentedTabs<Tab>
          label="Nội dung tài liệu"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "content", label: "Nội dung" },
            { id: "chapters", label: "Mục lục" },
            { id: "discussion", label: "Thảo luận" },
          ]}
        />
      </div>
      {tab === "content" && (
        <section className="rounded-panel border border-border bg-surface p-6">
          <div className="prose max-w-none whitespace-pre-wrap text-[15px] leading-7 text-ink">
            {state.content || "Tài liệu chưa có nội dung"}
          </div>
          {document.tags?.length > 0 && (
            <div className="mt-8 flex flex-wrap gap-2 border-t border-border pt-5">
              {document.tags.map((tag: string) => (
                <span
                  key={tag}
                  className="rounded-control bg-surface-quiet px-3 py-1.5 text-[12px] text-ink-muted"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </section>
      )}
      {tab === "chapters" &&
        (document.chapters?.length ? (
          <ol className="overflow-hidden rounded-panel border border-border bg-surface">
            {document.chapters.map((chapter: any, index: number) => (
              <li
                key={chapter.id ?? index}
                className="flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-b-0"
              >
                <span className="text-[14px] font-semibold text-ink">
                  {chapter.title || `Chương ${index + 1}`}
                </span>
                <span className="text-[12px] text-ink-muted">
                  {chapter.word_count
                    ? `${Number(chapter.word_count).toLocaleString("vi-VN")} từ`
                    : "Có thể đọc"}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <InlineState
            title="Chưa có mục lục"
          />
        ))}
      {tab === "discussion" && <DocumentDiscussion documentId={id} />}
    </div>
  );
}
