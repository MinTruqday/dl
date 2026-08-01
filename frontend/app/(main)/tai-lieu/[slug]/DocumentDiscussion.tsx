"use client";

import InlineState from "@/app/_components/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useDocumentDiscussion } from "./useDocumentDiscussion";

export default function DocumentDiscussion({
  documentId,
}: {
  documentId: string;
}) {
  const discussion = useDocumentDiscussion(documentId);

  return (
    <section>
      <div className="flex items-center justify-between border-b border-border pb-3">
        <h2 className="text-[15px] font-semibold text-ink">Thảo luận</h2>
        <span className="text-[12px] text-ink-muted">
          {discussion.comments.length} phản hồi
        </span>
      </div>

      {discussion.error && (
        <div className="mt-4">
          <InlineState
            title="Không thể xử lý thảo luận"
            detail={discussion.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={discussion.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      <form onSubmit={discussion.submit} className="mt-5">
        <label htmlFor="discussion-text" className="text-[13px] font-semibold">
          {discussion.replyTo ? "Trả lời phản hồi" : "Phản hồi mới"}
        </label>
        <textarea
          id="discussion-text"
          value={discussion.text}
          onChange={(event) => discussion.setText(event.target.value)}
          className="apple-input mt-2 min-h-24 w-full resize-y"
          disabled={discussion.submitting}
        />
        <div className="mt-2 flex justify-end gap-2">
          {discussion.replyTo && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => discussion.setReplyTo("")}
            >
              Hủy trả lời
            </Button>
          )}
          <Button
            type="submit"
            disabled={discussion.submitting || !discussion.text.trim()}
          >
            {discussion.submitting ? "Đang gửi" : "Gửi"}
          </Button>
        </div>
      </form>

      {discussion.loading ? (
        <div className="mt-6">
          <PageLoader rows={3} />
        </div>
      ) : discussion.comments.length ? (
        <ol className="mt-6 divide-y divide-border border-y border-border">
          {discussion.comments.map((comment) => {
            const depth = Math.max(
              0,
              (comment.path?.match(/,/g) || []).length - 1,
            );
            const name = comment.user?.full_name || "Độc giả";
            return (
              <li
                key={comment._id}
                className={depth ? "py-4 pl-6 md:pl-10" : "py-4"}
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-[13px] font-semibold text-ink">
                    {name}
                  </span>
                  <time className="text-[12px] text-ink-faint">
                    {new Date(comment.created_at).toLocaleDateString("vi-VN")}
                  </time>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-[14px] leading-6 text-ink-muted">
                  {comment.text || comment.content}
                </p>
                <button
                  type="button"
                  onClick={() => discussion.setReplyTo(comment._id)}
                  className="mt-2 text-[12px] font-semibold text-brand hover:text-brand-hover"
                >
                  Trả lời
                </button>
              </li>
            );
          })}
        </ol>
      ) : (
        <div className="mt-6">
          <InlineState title="Chưa có phản hồi" />
        </div>
      )}
    </section>
  );
}
