"use client";

import React, { useEffect } from "react";
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
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4 animate-in fade-in backdrop-blur-sm bg-black/40">
      <div
        className={cn(
          "bg-white w-full max-w-lg border border-[#D2D2D7] animate-in zoom-in-95 rounded-[24px] relative p-0 shadow-2xl",
          className,
        )}
      >
        {showCloseButton && (
          <button
            onClick={onClose}
            className="absolute top-5 right-5 text-[#6E6E73] hover:text-[#1D1D1F] transition-colors"
          >
            <X className="w-4 h-4" />
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
    <div className={cn("border-b border-[#E8E8ED] p-6 mb-0", className)}>
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
    <h3 className={cn("text-[20px] font-semibold text-[#1D1D1F] pr-8", className)}>
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
        "text-[13px] text-[#6E6E73] mt-1",
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
  return <div className={cn("p-5 space-y-4", className)}>{children}</div>;
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
        "flex gap-3 border-t border-[#E8E8ED] p-6 bg-[#F5F5F7] rounded-b-[24px] mt-0 space-y-0",
        className,
      )}
    >
      {children}
    </div>
  );
}
