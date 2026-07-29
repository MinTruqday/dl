import * as React from "react";
import { cn } from "../../lib/app_utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-11 w-full rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface)] px-3 text-[14px] text-[var(--ink)] outline-none transition placeholder:text-[var(--ink-faint)] focus:border-[var(--brand)] focus:ring-2 focus:ring-[var(--brand-soft)] disabled:cursor-not-allowed disabled:bg-[var(--surface-quiet)] disabled:opacity-70",
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = "Input";

export { Input };
