"use client";
import { useState, useEffect } from "react";
import Navigation from "@/shared/components/common/Navigation";
import Dock from "@/shared/components/common/Dock";
import { useAuth } from "@/features/auth/contexts/AuthContext";
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
    <div className="min-h-screen bg-zinc-50 text-black font-sans selection:bg-black selection:text-white overflow-x-hidden relative pb-28">
      <Navigation />
      
      <main
        className="relative px-2 md:px-4"
        style={{
          paddingTop: "calc(var(--navbar-height) + 32px)",
          minHeight: "100vh",
        }}
      >
        {children}
      </main>

      {/* MacOS Style Bottom Dock */}
      {mounted && <Dock />}
    </div>
  );
}
