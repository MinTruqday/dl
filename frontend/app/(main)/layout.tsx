"use client";

import { usePathname } from "next/navigation";
import AppShell from "@/app/_components/AppShell";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const isPublic = pathname.startsWith("/kham-pha") || pathname.startsWith("/tai-lieu/");

  return <AppShell requireAuth={!isPublic}>{children}</AppShell>;
}
