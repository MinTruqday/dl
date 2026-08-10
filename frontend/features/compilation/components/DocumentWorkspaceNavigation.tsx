"use client";

import { useSearchParams } from "next/navigation";
import RouteTabs from "@/shared/components/navigation/RouteTabs";

const sections = [
  { href: "/soan-thao/cau-hinh", label: "Cấu hình" },
  { href: "/soan-thao/binh-luan", label: "Bình luận" },
  { href: "/soan-thao/lich-su", label: "Phiên bản" },
  { href: "/soan-thao/so-lieu", label: "Số liệu" },
];

export default function DocumentWorkspaceNavigation() {
  const documentId = useSearchParams().get("tai-lieu") || "";
  const query = documentId ? `?tai-lieu=${encodeURIComponent(documentId)}` : "";

  return (
    <RouteTabs
      label="Công cụ tài liệu"
      items={[
        {
          href: `/soan-thao/chinh-sua${query}`,
          activePath: "/soan-thao/chinh-sua",
          label: "Soạn thảo",
        },
        ...sections.map((section) => ({
          href: `${section.href}${query}`,
          activePath: section.href,
          label: section.label,
        })),
      ]}
    />
  );
}
