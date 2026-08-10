import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  showTitle?: boolean;
  description?: string;
  actions?: ReactNode;
  meta?: ReactNode;
};

export default function PageHeader({
  title,
  showTitle = true,
  description,
  actions,
  meta,
}: PageHeaderProps) {
  if (!showTitle && !actions && !meta) {
    return <h1 className="sr-only">{title}</h1>;
  }

  return (
    <header className="mb-7">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h1
            className={
              showTitle
                ? "product-heading"
                : "sr-only"
            }
          >
            {title}
          </h1>
          {showTitle && description && (
            <p className="mt-2 max-w-[65ch] text-[14px] leading-relaxed text-ink-muted">
              {description}
            </p>
          )}
          {meta && (
            <div className="mt-2 text-[13px] text-ink-muted">{meta}</div>
          )}
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
