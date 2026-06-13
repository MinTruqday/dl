"use client";
import { useState, useEffect } from "react";
import Navigation from "./Navigation";
import Menu from "./Menu";
import { useAuth } from "@/features/auth/contexts/Auth";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

interface WorkspaceProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function Workspace({ children, requireAuth = false }: WorkspaceProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      } else {
        const saved = localStorage.getItem("doclib_sidebar_open");
        setSidebarOpen(saved !== "false");
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (requireAuth && !isLoading && !user) {
      router.push("/dang-nhap");
    }
  }, [requireAuth, isLoading, user, router]);

  const toggleSidebar = () => {
    if (isMobile) {
      setMobileMenuOpen((v) => !v);
    } else {
      const next = !sidebarOpen;
      setSidebarOpen(next);
      localStorage.setItem("doclib_sidebar_open", String(next));
    }
  };

  const sidebarIsOpen = mounted
    ? isMobile
      ? mobileMenuOpen
      : sidebarOpen
    : true;

  if (requireAuth && (isLoading || (!user && mounted))) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-black font-sans selection:bg-black selection:text-white overflow-x-hidden">
      <Navigation onToggleSidebar={toggleSidebar} />

      <Menu
        isOpen={sidebarIsOpen}
        onToggle={toggleSidebar}
        isMobileOverlay={isMobile}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <main
        className="relative pr-2 md:pr-4 pb-2 md:pb-4 transition-all duration-300"
        style={{
          paddingTop: isMobile ? "calc(var(--navbar-height) + 16px)" : "calc(var(--navbar-height) + 32px)",
          marginLeft: !mounted
            ? "calc(var(--sidebar-width-expanded) + 32px)"
            : isMobile
              ? "8px"
              : sidebarOpen
                ? "calc(var(--sidebar-width-expanded) + 32px)"
                : "calc(var(--sidebar-width-collapsed) + 32px)",
          minHeight: "100vh",
        }}
      >
        {children}
      </main>
    </div>
  );
}
