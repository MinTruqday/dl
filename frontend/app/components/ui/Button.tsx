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
  const vClass = {
    primary: "bg-black text-white border-black hover:bg-zinc-800",
    secondary: "bg-white text-black border-zinc-200 hover:border-black hover:bg-zinc-50",
    outline: "bg-transparent text-black border-zinc-200 hover:border-black hover:bg-zinc-50",
    ghost: "bg-transparent text-black border-transparent hover:bg-zinc-50",
    danger: "bg-zinc-50 text-black border-zinc-200 hover:bg-zinc-100 hover:border-black",
  };

  const sClass = {
    sm: "px-3 py-1.5 text-[11px] font-bold border",
    md: "px-5 py-2.5 text-xs font-bold border",
    lg: "px-8 py-3.5 text-sm font-bold border",
    icon: "p-2 border border-zinc-200 hover:border-black hover:bg-zinc-50",
  };

  return (
    <button
      className={`inline-flex items-center justify-center font-sans transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed rounded-none active:scale-[0.98] ${vClass[variant]} ${sClass[size]} ${className}`}
      {...props}
    >
      {icon && <span className={children ? "mr-2" : ""}>{icon}</span>}
      {children}
    </button>
  );
}
