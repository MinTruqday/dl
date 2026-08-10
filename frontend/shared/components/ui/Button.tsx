"use client";

import React from "react";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  icon?: React.ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  icon,
  ...props
}: ButtonProps) {
  const hasLabel = React.Children.toArray(children).some(
    (child) => typeof child === "string" || typeof child === "number",
  );
  const vClass = {
    primary:
      "border-brand bg-brand text-white hover:border-brand-hover hover:bg-brand-hover",
    secondary:
      "border-border-strong bg-surface text-ink hover:bg-surface-quiet",
    outline:
      "border-border-strong bg-transparent text-ink hover:bg-surface-quiet",
    ghost: "border-transparent bg-transparent text-ink hover:bg-surface-quiet",
    danger: "border-danger bg-danger text-white hover:bg-danger/90",
  };

  const sClass = {
    sm: "min-h-9 px-3 py-1.5 text-[13px] border",
    md: "min-h-11 px-4 py-2.5 text-[14px] border",
    lg: "min-h-12 px-5 py-3 text-[15px] border",
    icon: "h-11 w-11 border p-2",
  };

  return (
    <button
      className={`inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-control font-semibold transition duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-50 ${hasLabel ? "[&>svg]:hidden" : ""} ${vClass[variant]} ${sClass[size]} ${className}`}
      {...props}
    >
      {icon && !children && <span>{icon}</span>}
      {children}
    </button>
  );
}
