import React from "react";

export default function EmptyState({
  text = "Chưa có dữ liệu",
  description,
  action,
  compact = false,
}: {
  text?: string;
  description?: string;
  action?: React.ReactNode;
  compact?: boolean;
}) {
  return (
    <div
      className={`flex w-full flex-col items-start justify-center rounded-[var(--radius-panel)] border border-dashed border-[var(--border-strong)] bg-[var(--surface-raised)] px-6 ${
        compact ? "py-10" : "py-16"
      }`}
    >
      <p className="text-[16px] font-semibold text-[var(--ink)]">{text}</p>
      {description && (
        <p className="mt-1 max-w-[52ch] text-[14px] leading-6 text-[var(--ink-muted)]">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
