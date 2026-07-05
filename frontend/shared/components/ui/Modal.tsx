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
          "bg-[#F5F5F7] w-full max-w-md animate-in zoom-in-95 rounded-[18px] relative p-0 shadow-2xl border-none overflow-hidden",
          className,
        )}
      >
        {showCloseButton && (
          <button
            onClick={onClose}
            className="absolute top-6 right-6 p-1 text-[#6E6E73] hover:text-[#1D1D1F] transition-colors rounded-full hover:bg-[#E8E8ED]"
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
  return <div className={cn("p-6 space-y-4 bg-white", className)}>{children}</div>;
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
        "p-6 flex justify-end gap-3 border-t border-[#E8E8ED] rounded-b-[18px]",
        className,
      )}
    >
      {children}
    </div>
  );
}
