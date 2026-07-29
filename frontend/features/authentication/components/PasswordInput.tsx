"use client";

import { ChangeEvent, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function PasswordInput({
  id,
  value,
  onChange,
  autoComplete,
  required = false,
}: {
  id: string;
  value: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  autoComplete: string;
  required?: boolean;
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <input
        id={id}
        name={id}
        type={visible ? "text" : "password"}
        autoComplete={autoComplete}
        required={required}
        value={value}
        onChange={onChange}
        className="field-control w-full pr-12"
      />
      <button
        type="button"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
        className="absolute right-1 top-1 flex size-9 items-center justify-center rounded-[var(--radius-control)] text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]"
      >
        {visible ? (
          <EyeOff aria-hidden="true" className="size-[18px]" strokeWidth={1.75} />
        ) : (
          <Eye aria-hidden="true" className="size-[18px]" strokeWidth={1.75} />
        )}
      </button>
    </div>
  );
}
