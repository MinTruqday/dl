"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, PenTool } from "lucide-react";
import { useAuth } from "@/contexts/Auth";

export default function CreationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const isAdminOrMod = user?.role === "admin" || user?.role === "moderator";

  const navItems = [
    { id: "step1", label: "Thông tin sơ bộ", href: "/khoi-tao" },
    { id: "step2", label: "Kho lưu trữ nháp", href: "/khoi-tao/ban-thao" },
    ...(isAdminOrMod ? [{ id: "step3", label: "Duyệt bản thảo", href: "/khoi-tao/duyet-ban-thao" }] : []),
  ];

  const isActive = (href: string) => {
    if (href === "/khoi-tao") return pathname === "/khoi-tao";
    return pathname === href;
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] font-sans text-black selection:bg-black selection:text-white">
      <div className="grid lg:grid-cols-12 gap-6 h-full">
        <aside className="lg:col-span-3 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-4">
            <div className="text-sm font-semibold text-black mb-1">
              Sáng tác
            </div>
            <nav className="flex flex-col gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-xl transition-colors ${
                    isActive(item.href)
                      ? "bg-zinc-100 text-black"
                      : "bg-white text-zinc-500 hover:bg-zinc-50"
                  }`}
                >
                  {item.label}
                  {isActive(item.href) && <ChevronRight className="w-4 h-4" />}
                </Link>
              ))}
            </nav>
          </div>
        </aside>

        <main className="lg:col-span-9 h-full overflow-y-auto pr-2 custom-scrollbar">
          <div className="border border-zinc-200 bg-white p-5 rounded-2xl shadow-sm min-h-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
