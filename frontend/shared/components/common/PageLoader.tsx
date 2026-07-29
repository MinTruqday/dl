import React from "react";

export default function PageLoader({
  text = "Đang tải dữ liệu",
}: {
  text?: string;
}) {
  return (
    <div className="min-h-[100dvh] bg-[var(--canvas)] px-4 py-20">
      <div className="mx-auto w-full max-w-4xl">
        <p className="mb-6 text-[14px] text-[var(--ink-muted)]">{text}</p>
        <div className="space-y-4" aria-hidden="true">
          <div className="h-8 w-48 rounded-[var(--radius-control)] bg-[var(--surface-quiet)]" />
          <div className="h-4 w-full max-w-xl rounded-[var(--radius-control)] bg-[var(--surface-quiet)]" />
          <div className="mt-8 h-44 w-full rounded-[var(--radius-panel)] bg-[var(--surface-quiet)]" />
        </div>
      </div>
    </div>
  );
}
