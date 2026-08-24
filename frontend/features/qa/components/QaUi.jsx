"use client";
import Link from "next/link";
import { statusLabel } from "../lib/qa";

export function QaPage({ eyebrow, title, description, actions, children }) {
  return (
    <div className="mx-auto w-full max-w-[1450px] space-y-6 p-5 md:p-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[12px] font-semibold uppercase tracking-[0.16em] text-brand">
            {eyebrow}
          </p>
          <h1 className="mt-2 text-[30px] font-semibold tracking-[-0.035em]">{title}</h1>
          {description && (
            <p className="mt-2 max-w-3xl text-[14px] leading-6 text-ink-muted">{description}</p>
          )}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </header>
      {children}
    </div>
  );
}

export function Panel({ title, description, actions, children, className = "" }) {
  return (
    <section className={`rounded-panel border border-border bg-surface ${className}`}>
      {(title || actions) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
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

export function Metric({ label, value, detail }) {
  return (
    <section className="rounded-panel border border-border bg-surface p-5">
      <p className="text-[28px] font-semibold">{value}</p>
      <p className="mt-1 text-[12px] font-semibold text-ink-muted">{label}</p>
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
