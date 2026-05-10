"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, PenTool } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function KhoiTaoLayout({
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Khởi tạo nội dung</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Khởi tạo & Thiết lập không gian soạn thảo
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Sáng tác
            </div>
            <nav className="flex flex-col gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none transition-colors ${
                    isActive(item.href)
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent hover:bg-zinc-50"
                  }`}
                >
                  {item.label}
                  {isActive(item.href) && <ChevronRight className="w-4 h-4" />}
                </Link>
              ))}
            </nav>
          </div>

        </aside>

        <main className="lg:col-span-9">{children}</main>
      </div>
    </div>
  );
}
