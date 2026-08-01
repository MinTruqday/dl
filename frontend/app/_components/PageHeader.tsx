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
  showTitle = false,
  description,
  actions,
  meta,
}: PageHeaderProps) {
  if (!showTitle && !actions && !meta) {
    return <h1 className="sr-only">{title}</h1>;
  }

  return (
    <header className="mb-5 border-b border-border pb-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h1
            className={
              showTitle
                ? "text-[19px] font-semibold tracking-[-0.015em] text-ink"
                : "sr-only"
            }
          >
            {title}
          </h1>
          {showTitle && description && (
            <p className="product-description">{description}</p>
          )}
          {meta && (
            <div className="mt-2 text-[13px] text-ink-muted">{meta}</div>
          )}
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
