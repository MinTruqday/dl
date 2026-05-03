"use client";
import { useState, useEffect } from "react";
import Navigation from "./Navigation";
import Menu from "./Menu";

interface AppShellProps {
  children: React.ReactNode;
}

export default function Workspace({ children }: AppShellProps) {
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

  const sidebarIsOpen = mounted
    ? isMobile
      ? mobileMenuOpen
      : sidebarOpen
    : true;

  return (
    <div className="min-h-screen bg-white text-black font-sans selection:bg-black selection:text-white animate-in fade-in ">
      <Navigation onToggleSidebar={toggleSidebar} />

      <Menu
        isOpen={sidebarIsOpen}
        onToggle={toggleSidebar}
        isMobileOverlay={isMobile}
        onMobileClose={() => setMobileMenuOpen(false)}
      />

      <main
        className=" ease-in-out"
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
        <div className="animate-in slide-in-from-bottom-4 ">{children}</div>
      </main>
    </div>
  );
}
