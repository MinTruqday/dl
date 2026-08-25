"use client";
import Link from "next/link";
import { statusLabel } from "../lib/qa";

export function QaPage({ title, description, actions, children }) {
  return (
    <div className="mx-auto w-full max-w-[1480px] space-y-7 p-4 sm:p-6 md:p-9">
      <header className="flex flex-col gap-5 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <h1 className="text-[30px] font-semibold leading-[1.08] tracking-[-0.045em] md:text-[38px]">
            {title}
          </h1>
          {description && (
            <p className="mt-3 max-w-3xl text-[14px] leading-7 text-ink-muted">{description}</p>
          )}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </header>
      {children}
    </div>
  );
}

export function Panel({ title, description, actions, children, className = "" }) {
  return (
    <section
      className={`overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_8px_24px_rgba(48,47,42,0.04)] ${className}`}
    >
      {(title || actions) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface-raised px-5 py-4">
          <div>
            {title && <h2 className="font-semibold">{title}</h2>}
            {description && <p className="mt-1 text-[12px] text-ink-muted">{description}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function StatusPill({ value }) {
  return (
    <span className="inline-flex rounded-full bg-brand-soft px-2.5 py-1 text-[11px] font-semibold text-brand">
      {statusLabel(value)}
    </span>
  );
}

export function EmptyState({ children, actionHref, actionLabel }) {
  return (
    <div className="p-10 text-center text-[13px] text-ink-muted">
      <p>{children}</p>
      {actionHref && (
        <Link href={actionHref} className="apple-button mt-4">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

export function LoadingState() {
  return <div className="skeleton h-56" />;
}

export function ErrorState({ message }) {
  return (
    <p role="alert" className="rounded-control bg-danger-soft p-4 text-[13px] text-danger">
      {message}
    </p>
  );
}

export function DegradedBanner({ mode, message }) {
  if (!mode || mode === "NORMAL") return null;
  return (
    <p
      role="status"
      className="rounded-control border border-warning/30 bg-warning-soft p-4 text-[13px] text-warning"
    >
      {message ||
        `Hệ thống đang ở chế độ ${mode} các thao tác lõi vẫn được lưu và có thể cần kiểm tra thủ công`}
    </p>
  );
}

export function Metric({ label, value, detail }) {
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 shadow-[0_8px_20px_rgba(48,47,42,0.035)] sm:p-5">
      <p className="text-[30px] font-semibold tracking-[-0.04em]">{value}</p>
      <p className="mt-2 text-[12px] font-semibold leading-5 text-ink-muted">{label}</p>
      {detail && <p className="mt-2 text-[11px] text-ink-faint">{detail}</p>}
    </section>
  );
}

export function ProjectCrumb({ projectId, projectName }) {
  return (
    <Link className="text-[13px] font-semibold text-brand" href={`/qa/projects/${projectId}`}>
      {projectName || "Về dự án"}
    </Link>
  );
}
