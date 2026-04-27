"use client";

import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  icon?: React.ReactNode;
}

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  children, 
  icon,
  ...props 
}: ButtonProps) {
  
  const vClass = {
    primary: 'bg-black text-white border-black hover:bg-zinc-800',
    secondary: 'bg-white text-black border-black hover:bg-zinc-50',
    outline: 'bg-transparent text-black border-black hover:bg-zinc-50',
    ghost: 'bg-transparent text-black border-transparent hover:bg-zinc-50',
    danger: 'bg-zinc-50 text-black border-black hover:bg-zinc-100'
  };

  const sClass = {
    sm: 'px-3 py-1.5 text-[12px] font-bold tracking-widest border',
    md: 'px-5 py-2.5 text-xs font-bold tracking-widest border',
    lg: 'px-8 py-4 text-sm font-bold tracking-widest border border-2',
    icon: 'p-2 border hover:bg-zinc-100'
  };

  return (
    <button 
      className={`inline-flex items-center justify-center font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed rounded-none ${vClass[variant]} ${sClass[size]} ${className}`}
      {...props}
    >
      {icon && <span className={children ? "mr-2" : ""}>{icon}</span>}
      {children}
    </button>
  );
}
