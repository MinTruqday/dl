"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Bookmark, Flag, Share2 } from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import DocumentDiscussion from "./DocumentDiscussion";
import ReportDialog from "./ReportDialog";
import { useDocumentDetails } from "./useDocumentDetails";

type Tab = "content" | "chapters" | "discussion";
export default function DocumentDetailsPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const state = useDocumentDetails(slug);
  const [tab, setTab] = useState<Tab>("content");
  const [reportOpen, setReportOpen] = useState(false);
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
  const premiumLocked = document.is_premium && !document.has_purchased;
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
            <Button
              size="icon"
              variant="secondary"
              aria-label="Báo cáo"
              onClick={() => setReportOpen(true)}
            >
              <Flag size={17} />
            </Button>
            {premiumLocked ? (
              <Button disabled={state.processing} onClick={state.purchase}>
                {state.processing
                  ? "Đang xử lý"
                  : `Mua ${document.price_dl || 0} dl`}
              </Button>
            ) : (
              <Button onClick={() => router.push(`/tai-lieu/xem-truoc/${id}`)}>
                Đọc tài liệu
              </Button>
            )}
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
            {premiumLocked
              ? "Mua tài liệu để đọc toàn bộ nội dung"
              : state.content || "Tài liệu chưa có nội dung"}
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
                    : chapter.is_premium
                      ? "Trả phí"
                      : "Có thể đọc"}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <InlineState
            title="Chưa có mục lục"
            detail="Tài liệu này chưa được chia thành chương"
          />
        ))}
      {tab === "discussion" && <DocumentDiscussion documentId={id} />}
      {reportOpen && (
        <ReportDialog
          onSubmit={state.report}
          onClose={() => setReportOpen(false)}
        />
      )}
    </div>
  );
}
