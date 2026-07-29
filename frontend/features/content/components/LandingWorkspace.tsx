"use client";

import { useMemo, useState } from "react";

const initialText =
  "Một ý tưởng tốt không bắt đầu bằng mẫu có sẵn\n\nNó bắt đầu bằng một khoảng trống đủ yên để bạn nghĩ và đủ linh hoạt để cùng người khác hoàn thiện"

export default function LandingWorkspace() {
  const [title, setTitle] = useState("Bản thảo mới");
  const [text, setText] = useState(initialText);
  const wordCount = useMemo(
    () => text.trim().split(/\s+/).filter(Boolean).length,
    [text],
  );

  return (
    <div className="relative">
      <div className="absolute -inset-6 -z-10 rounded-[40px] bg-[var(--brand-soft)] opacity-70 blur-2xl" />
      <div className="overflow-hidden rounded-[var(--radius-workspace)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_28px_90px_rgba(47,93,80,0.13)]">
        <div className="flex min-h-12 items-center justify-between border-b border-[var(--border)] px-4">
          <span className="text-[13px] font-semibold text-[var(--ink)]">
            DocLib
          </span>
          <span className="text-[12px] text-[var(--ink-faint)]">
            {wordCount} từ
          </span>
        </div>
        <div className="grid min-h-[430px] sm:grid-cols-[140px_1fr]">
          <div className="hidden border-r border-[var(--border)] bg-[var(--surface-raised)] p-3 sm:block">
            <p className="px-2 py-2 text-[12px] font-medium text-[var(--ink-faint)]">
              Gần đây
            </p>
            <button
              type="button"
              className="w-full rounded-[var(--radius-control)] bg-[var(--brand-soft)] px-2 py-2 text-left text-[13px] font-semibold text-[var(--brand)]"
            >
              Bản thảo mới
            </button>
            <button
              type="button"
              className="mt-1 w-full rounded-[var(--radius-control)] px-2 py-2 text-left text-[13px] text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)]"
            >
              Ghi chú đọc
            </button>
          </div>
          <div className="flex min-w-0 flex-col p-6 sm:p-8">
            <label htmlFor="landing-title" className="sr-only">
              Tiêu đề tài liệu
            </label>
            <input
              id="landing-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="w-full border-0 bg-transparent text-[28px] font-semibold tracking-[-0.035em] text-[var(--ink)] outline-none"
            />
            <div className="my-5 h-px bg-[var(--border)]" />
            <label htmlFor="landing-body" className="sr-only">
              Nội dung tài liệu
            </label>
            <textarea
              id="landing-body"
              value={text}
              onChange={(event) => setText(event.target.value)}
              className="min-h-[230px] w-full flex-1 resize-none border-0 bg-transparent text-[15px] leading-7 text-[var(--ink)] outline-none"
            />
            <div className="mt-5 flex items-center justify-between border-t border-[var(--border)] pt-4">
              <span className="text-[12px] text-[var(--ink-faint)]">
                Thử chỉnh nội dung ngay tại đây
              </span>
              <button
                type="button"
                onClick={() => {
                  setTitle("Bản thảo mới");
                  setText(initialText);
                }}
                className="min-h-9 rounded-[var(--radius-control)] px-3 text-[13px] font-medium text-[var(--brand)] hover:bg-[var(--brand-soft)]"
              >
                Đặt lại
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
