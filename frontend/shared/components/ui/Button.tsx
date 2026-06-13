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
    primary: "bg-black text-white border-black ",
    secondary: "bg-white text-black border-zinc-200 ",
    outline: "bg-transparent text-black border-zinc-200 ",
    ghost: "bg-transparent text-black border-transparent ",
    danger: "bg-white text-black border-zinc-200 ",
  };

  const sClass = {
    sm: "px-3 py-1.5 text-[11px] font-bold border",
    md: "px-5 py-2.5 text-xs font-bold border",
    lg: "px-8 py-3.5 text-sm font-bold border",
    icon: "p-2 border border-zinc-200 ",
  };

  return (
    <button
      className={`inline-flex items-center justify-center font-sans disabled:opacity-50 disabled:cursor-not-allowed rounded-none ${vClass[variant]} ${sClass[size]} ${className}`}
      {...props}
    >
      {icon && <span className={children ? "mr-2" : ""}>{icon}</span>}
      {children}
    </button>
  );
}
