"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  showCloseButton?: boolean;
}

export function Modal({
  isOpen,
  onClose,
  children,
  className,
  showCloseButton = true,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      document.body.style.overflow = "hidden";
      const frame = requestAnimationFrame(() => dialogRef.current?.focus());
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") onCloseRef.current();
        if (event.key !== "Tab" || !dialogRef.current) return;
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      };
      document.addEventListener("keydown", handleKeyDown);
      return () => {
        cancelAnimationFrame(frame);
        document.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "";
        previousFocusRef.current?.focus();
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-ink/30 p-4 backdrop-blur-[2px] animate-in fade-in"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        tabIndex={-1}
        className={cn(
          "relative w-full max-w-md overflow-hidden rounded-panel border border-border bg-surface p-0 shadow-[0_24px_80px_rgba(32,32,30,0.18)] outline-none animate-in zoom-in-95",
          className,
        )}
      >
        {showCloseButton && (
          <button
            onClick={onClose}
            className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-control text-ink-muted transition-colors hover:bg-surface-quiet hover:text-ink"
            aria-label="Đóng"
          >
            <X className="w-5 h-5" />
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
    <div className={cn("border-b border-border p-6 pr-16", className)}>
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
    <h3
      className={cn(
        "text-[20px] font-semibold tracking-[-0.02em] text-ink",
        className,
      )}
    >
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
    <p
      className={cn(
        "mt-1 text-[14px] leading-relaxed text-ink-muted",
        className,
      )}
    >
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
  return (
    <div className={cn("space-y-4 bg-surface p-6", className)}>{children}</div>
  );
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
        "flex justify-end gap-3 border-t border-border bg-surface-raised p-6",
        className,
      )}
    >
      {children}
    </div>
  );
}
