"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Navigation from "@/shared/components/common/Navigation";
import Dock from "@/shared/components/common/Dock";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import PageLoader from "@/shared/components/common/PageLoader";

interface WorkspaceProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function Workspace({
  children,
  requireAuth = false,
}: WorkspaceProps) {
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();

  useEffect(() => {
    if (requireAuth && !isLoading && !user) {
      router.replace("/dang-nhap");
    }
  }, [requireAuth, isLoading, user, router]);

  if (requireAuth && (isLoading || !user)) {
    return <PageLoader text="Đang mở không gian làm việc" />;
  }

  return (
    <div className="min-h-[100dvh] bg-[var(--canvas)] text-[var(--ink)]">
      <Navigation />
      <Dock />
      <main className="min-h-[100dvh] pt-[var(--topbar-height)] lg:pl-[var(--sidebar-width)]">
        <div className="mx-auto flex min-h-[calc(100dvh-var(--topbar-height))] w-full max-w-[1280px] flex-col px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
