"use client";
import { useState, useEffect } from "react";
import Navigation from "@/shared/components/common/Navigation";
import Dock from "@/shared/components/common/Dock";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

interface WorkspaceProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function Workspace({
  children,
  requireAuth = false,
}: WorkspaceProps) {
  const [mounted, setMounted] = useState(false);
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (requireAuth && !isLoading && !user) {
      router.push("/dang-nhap");
    }
  }, [requireAuth, isLoading, user, router]);

  if (requireAuth && (isLoading || (!user && mounted))) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="h-[100dvh] bg-[#FFFFFF] md:bg-[#F5F5F7] text-[#1D1D1F] font-sans selection:bg-[#0071E3] selection:text-white flex flex-col overflow-hidden relative">
      <Navigation />

      <main className="flex-1 flex flex-col items-center min-h-0 pt-[56px] pb-24 md:pb-0 relative lg:pl-[56px]">
        <div className="w-full max-w-[1200px] mx-auto px-4 md:px-6 py-6 flex-1 flex flex-col min-h-0 overflow-hidden">
          {children}
        </div>
      </main>

      {mounted && <Dock />}
    </div>
  );
}
