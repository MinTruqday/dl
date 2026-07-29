"use client";

import React from "react";
import { cn } from "../../lib/app_utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  const variants = {
    primary:
      "border-[var(--brand)] bg-[var(--brand)] text-white hover:border-[var(--brand-hover)] hover:bg-[var(--brand-hover)]",
    secondary:
      "border-[var(--border)] bg-[var(--surface)] text-[var(--ink)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-quiet)]",
    ghost:
      "border-transparent bg-transparent text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]",
    danger:
      "border-[var(--danger)] bg-[var(--danger)] text-white hover:brightness-95",
  };
  const sizes = {
    sm: "min-h-9 px-3 text-[13px]",
    md: "min-h-10 px-4 text-[14px]",
    lg: "min-h-11 px-5 text-[15px]",
    icon: "size-10 p-0",
  };

  return (
    <button
      className={cn(
        "inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-[var(--radius-control)] border font-semibold transition duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
