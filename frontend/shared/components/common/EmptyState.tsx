import Link from "next/link";

type EmptyStateProps = {
  text?: string;
  description?: string;
  compact?: boolean;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
};

export default function EmptyState({
  text = "Chưa có dữ liệu",
  description,
  compact = false,
  actionLabel,
  actionHref,
  onAction,
}: EmptyStateProps) {
  const actionClass =
    "mt-5 inline-flex min-h-11 items-center justify-center whitespace-nowrap rounded-control bg-brand px-4 py-2.5 text-[14px] font-semibold text-white transition duration-150 hover:bg-brand-hover active:translate-y-px";

  return (
    <div
      className={`${compact ? "py-10" : "py-16"} flex w-full flex-col items-start justify-center rounded-panel border border-border bg-surface px-5 md:px-8`}
    >
      <p className="text-[16px] font-semibold text-ink">{text}</p>
      {description && (
        <p className="mt-2 max-w-[58ch] text-[14px] leading-relaxed text-ink-muted">
          {description}
        </p>
      )}
      {actionLabel && actionHref && (
        <Link href={actionHref} className={actionClass}>
          {actionLabel}
        </Link>
      )}
      {actionLabel && onAction && !actionHref && (
        <button type="button" onClick={onAction} className={actionClass}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
