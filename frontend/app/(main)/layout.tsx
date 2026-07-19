"use client";

import Workspace from "@/features/content/components/Workspace";
import { usePathname } from "next/navigation";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const isPublic = () => {
    if (pathname === "/") return true;
    if (pathname.startsWith("/kham-pha")) return true;

    if (pathname.startsWith("/author")) return true;
    if (pathname.startsWith("/search")) return true;

    if (pathname.startsWith("/tai-lieu/")) {
      return true;
    }

    return false;
  };

  return <Workspace requireAuth={!isPublic()}>{children}</Workspace>;
}
