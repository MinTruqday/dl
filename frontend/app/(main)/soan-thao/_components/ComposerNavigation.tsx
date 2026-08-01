"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/soan-thao", label: "Tổng quan" },
  { href: "/soan-thao/ban-thao", label: "Bản thảo" },
  { href: "/soan-thao/khoi-tao", label: "Tạo mới" },
  { href: "/soan-thao/thung-rac", label: "Thùng rác" },
];

export default function ComposerNavigation() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Quản lý soạn thảo"
      className="mb-5 flex gap-1 overflow-x-auto border-b border-border"
    >
      {items.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap border-b-2 px-3 py-3 text-[13px] font-semibold ${
              active
                ? "border-brand text-brand"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
