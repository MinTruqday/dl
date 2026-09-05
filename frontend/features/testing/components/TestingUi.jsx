"use client";
import Link from "next/link";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { statusLabel } from "../lib/testing";

export function useQaActionDialog() {
  const titleId = useId();
  const dialogRef = useRef(null);
  const previousFocusRef = useRef(null);
  const [state, setState] = useState(null);
  const [values, setValues] = useState({});
  const ask = useCallback(
    (options) =>
      new Promise((resolve) => {
        const fields = options.fields || [];
        setValues(
          Object.fromEntries(fields.map((field) => [field.name, field.initialValue || ""])),
        );
        setState({ ...options, resolve });
      }),
    [],
  );
  useEffect(() => {
    if (!state) return undefined;
    previousFocusRef.current = document.activeElement;
    const dialogElement = dialogRef.current;
    const focusableSelector =
      'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex="-1"])';
    const focusable = () => Array.from(dialogElement?.querySelectorAll(focusableSelector) || []);
    const first = focusable()[0];
    first?.focus();
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        state.resolve(null);
        setState(null);
        return;
      }
      if (event.key !== "Tab") return;
      const elements = focusable();
      if (!elements.length) {
        event.preventDefault();
        dialogElement?.focus();
        return;
      }
      const firstElement = elements[0];
      const lastElement = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus?.();
    };
  }, [state]);
  const close = (result) => {
    state?.resolve(result);
    setState(null);
  };
  const dialog = state ? (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/45 p-4"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) close(null);
      }}
    >
      <section
        aria-labelledby={titleId}
        aria-modal="true"
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-border bg-surface p-6 shadow-2xl"
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        <h2 className="text-xl font-semibold" id={titleId}>
          {state.title}
        </h2>
        {state.description && (
          <p className="mt-2 text-[13px] leading-6 text-ink-muted">{state.description}</p>
        )}
        <form
          className="mt-5 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            close(values);
          }}
        >
          {(state.fields || []).map((field) => (
            <label className="field-label block" key={field.name}>
              {field.label}
              {field.options ? (
                <select
                  autoFocus={field.autoFocus}
                  className="apple-input mt-2"
                  required={field.required}
                  value={values[field.name] || ""}
                  onChange={(event) =>
                    setValues((current) => ({ ...current, [field.name]: event.target.value }))
                  }
                >
                  {field.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : field.multiline ? (
                <textarea
                  autoFocus={field.autoFocus}
                  className="apple-input mt-2 min-h-28"
                  required={field.required}
                  value={values[field.name] || ""}
                  onChange={(event) =>
                    setValues((current) => ({ ...current, [field.name]: event.target.value }))
                  }
                />
              ) : (
                <input
                  autoFocus={field.autoFocus}
                  className="apple-input mt-2"
                  required={field.required}
                  value={values[field.name] || ""}
                  onChange={(event) =>
                    setValues((current) => ({ ...current, [field.name]: event.target.value }))
                  }
                />
              )}
            </label>
          ))}
          <div className="flex justify-end gap-2 pt-2">
            <button className="secondary-button" type="button" onClick={() => close(null)}>
              Hủy
            </button>
            <button className={state.danger ? "danger-button" : "apple-button"} type="submit">
              {state.confirmLabel || "Xác nhận"}
            </button>
          </div>
        </form>
      </section>
    </div>
  ) : null;
  return { ask, dialog };
}

export function QaPage({ title, description, actions, children }) {
  return (
    <div className="mx-auto w-full max-w-[1480px] space-y-7 p-4 sm:p-6 md:p-9">
      <header className="flex flex-col gap-5 border-b border-border pb-6 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <h1 className="break-words text-[30px] font-semibold leading-[1.08] tracking-[-0.045em] md:text-[38px]">
            {title}
          </h1>
          {description && (
            <p className="mt-3 max-w-3xl text-[14px] leading-7 text-ink-muted">{description}</p>
          )}
        </div>
        {actions && <div className="flex max-w-full flex-wrap items-center gap-2">{actions}</div>}
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
          <div className="min-w-0 flex-1">
            {title && <h2 className="break-words font-semibold">{title}</h2>}
            {description && (
              <p className="mt-1 break-words text-[12px] leading-5 text-ink-muted">{description}</p>
            )}
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

export function EmptyState({ children, actionHref, actionLabel, onAction }) {
  return (
    <div className="p-10 text-center text-[13px] text-ink-muted">
      <p>{children}</p>
      {onAction ? (
        <button type="button" className="apple-button mt-4" onClick={onAction}>
          {actionLabel}
        </button>
      ) : actionHref ? (
        <Link href={actionHref} className="apple-button mt-4">
          {actionLabel}
        </Link>
      ) : null}
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
    <Link className="text-[13px] font-semibold text-brand" href={`/du-an/${projectId}`}>
      {projectName || "Về dự án"}
    </Link>
  );
}

export function Pagination({ value, page, pageSize, total, onChange }) {
  const pagination = value || {
    page,
    total,
    total_pages: Math.max(1, Math.ceil(total / pageSize)),
  };
  if (!pagination || pagination.total_pages <= 1) return null;
  return (
    <nav
      aria-label="Phân trang"
      className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-4"
    >
      <p className="text-[12px] text-ink-muted">
        Trang {pagination.page} trên {pagination.total_pages} với {pagination.total} kết quả
      </p>
      <div className="flex gap-2">
        <button
          aria-label="Trang trước"
          className="secondary-button"
          disabled={pagination.page <= 1}
          type="button"
          onClick={() => onChange(pagination.page - 1)}
        >
          Trang trước
        </button>
        <button
          aria-label="Trang sau"
          className="secondary-button"
          disabled={pagination.page >= pagination.total_pages}
          type="button"
          onClick={() => onChange(pagination.page + 1)}
        >
          Trang sau
        </button>
      </div>
    </nav>
  );
}
