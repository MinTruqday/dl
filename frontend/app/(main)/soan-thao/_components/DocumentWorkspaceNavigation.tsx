"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const sections = [
  { href: "/soan-thao/cau-hinh", label: "Cấu hình" },
  { href: "/soan-thao/binh-luan", label: "Bình luận" },
  { href: "/soan-thao/lich-su", label: "Phiên bản" },
  { href: "/soan-thao/so-lieu", label: "Số liệu" },
];

export default function DocumentWorkspaceNavigation() {
  const pathname = usePathname();
  const documentId = useSearchParams().get("tai-lieu") || "";
  const query = documentId ? `?tai-lieu=${encodeURIComponent(documentId)}` : "";

  return (
    <nav
      aria-label="Công cụ tài liệu"
      className="mb-5 flex items-center gap-1 overflow-x-auto border-b border-border"
    >
      <Link
        href={`/soan-thao/chinh-sua${query}`}
        className="mr-2 whitespace-nowrap border-b-2 border-transparent px-3 py-3 text-[13px] font-semibold text-brand"
      >
        Mở trình soạn thảo
      </Link>
      {sections.map((section) => {
        const active = pathname === section.href;
        return (
          <Link
            key={section.href}
            href={`${section.href}${query}`}
            aria-current={active ? "page" : undefined}
            className={`whitespace-nowrap border-b-2 px-3 py-3 text-[13px] font-semibold ${
              active
                ? "border-brand text-brand"
                : "border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {section.label}
          </Link>
        );
      })}
    </nav>
  );
}
