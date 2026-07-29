"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "../../lib/app_utils";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  showCloseButton?: boolean;
  closeOnBackdrop?: boolean;
}

export function Modal({
  isOpen,
  onClose,
  children,
  className,
  showCloseButton = true,
  closeOnBackdrop = true,
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", close);
    requestAnimationFrame(() => panelRef.current?.focus());
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", close);
      previous?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-[color:rgba(32,32,30,0.36)] p-4 backdrop-blur-[2px]"
      onMouseDown={(event) => {
        if (closeOnBackdrop && event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        tabIndex={-1}
        className={cn(
          "relative max-h-[min(88dvh,760px)] w-full max-w-lg overflow-y-auto rounded-[var(--radius-workspace)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_28px_80px_rgba(32,32,30,0.18)] outline-none",
          className,
        )}
      >
        {showCloseButton && (
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 z-10 min-h-9 rounded-[var(--radius-control)] px-3 text-[13px] font-medium text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]"
          >
            Đóng
          </button>
        )}
        {children}
      </div>
    </div>
  );
}

export function ModalHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("border-b border-[var(--border)] px-6 py-5 pr-20", className)}>
      {children}
    </div>
  );
}

export function ModalTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={cn("text-[20px] font-semibold tracking-[-0.02em] text-[var(--ink)]", className)}>
      {children}
    </h3>
  );
}

export function ModalDescription({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={cn("mt-1 text-[14px] leading-6 text-[var(--ink-muted)]", className)}>
      {children}
    </p>
  );
}

export function ModalContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("space-y-4 px-6 py-5", className)}>{children}</div>;
}

export function ModalFooter({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap justify-end gap-2 border-t border-[var(--border)] bg-[var(--surface-raised)] px-6 py-4",
        className,
      )}
    >
      {children}
    </div>
  );
}
