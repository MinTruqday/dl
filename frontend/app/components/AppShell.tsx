"use client";
import { useState, useEffect } from "react";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

interface AppShellProps {
  children: React.ReactNode;
}

let globalSidebarOpen: boolean | null = null;

export default function AppShell({ children }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

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

  const toggleSidebar = () => {
    if (isMobile) {
      setMobileMenuOpen((v) => !v);
    } else {
      const next = !sidebarOpen;
      setSidebarOpen(next);
      localStorage.setItem("doclib_sidebar_open", String(next));
    }
  };

  const sidebarIsOpen = mounted ? (isMobile ? mobileMenuOpen : sidebarOpen) : true;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar onToggleSidebar={toggleSidebar} />

      <Sidebar
        isOpen={sidebarIsOpen}
        onToggle={toggleSidebar}
        isMobileOverlay={isMobile}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <main
        className="transition-all duration-[250ms]"
        style={{
          paddingTop: "var(--navbar-height)",
          marginLeft: !mounted 
            ? "var(--sidebar-width-expanded)"
            : isMobile
            ? 0
            : sidebarOpen
            ? "var(--sidebar-width-expanded)"
            : "var(--sidebar-width-collapsed)",
          minHeight: "100vh",
        }}
      >
        {children}
      </main>
    </div>
  );
}
