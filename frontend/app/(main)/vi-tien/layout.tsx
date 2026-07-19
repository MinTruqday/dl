"use client";

import React from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Wallet, ArrowUpRight, ArrowDownLeft, ChevronRight } from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";

export default function WalletLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading: authLoading } = useAuth() as any;
  const pathname = usePathname();

  if (authLoading) return <PageLoader />;

  const navigationSections = [
    {
      title: "Giao dịch",
      items: [
        { id: "overview", label: "Tổng quan", icon: Wallet, href: "/vi-tien/tong-quan" },
        { id: "topup", label: "Nạp tiền", icon: ArrowDownLeft, href: "/vi-tien/nap-tien" },
        { id: "withdraw", label: "Rút tiền", icon: ArrowUpRight, href: "/vi-tien/rut-tien" },
      ],
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F5F5F7]">
      <div className="max-w-6xl w-full mx-auto px-4 md:px-8 py-8 flex-1 flex flex-col md:flex-row md:items-start gap-8">
        <aside className="w-full md:w-[260px] shrink-0 space-y-6">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0">
            {navigationSections.map((group, gIdx) => (
              <div key={gIdx} className="mb-8 last:mb-0">
                <p className="text-[13px] font-medium text-[#6E6E73] mb-4 uppercase tracking-wider">
                  {group.title}
                </p>
                <nav className="flex flex-col gap-1.5">
                  {group.items.map((section) => {
                    const active = pathname === section.href;
                    const Icon = section.icon;
                    return (
                      <Link
                        key={section.id}
                        href={section.href}
                        className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${active ? "bg-white text-[#0071E3] font-medium shadow-sm border border-[#E8E8ED]" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className={`w-4 h-4 ${active ? "text-[#0071E3]" : "text-[#86868B]"}`} />
                          <span className="truncate text-left">{section.label}</span>
                        </div>
                        {active && <ChevronRight className="w-4 h-4 shrink-0" />}
                      </Link>
                    );
                  })}
                </nav>
              </div>
            ))}
          </div>
        </aside>

        <main className="flex-1 min-w-0 bg-[#F5F5F7] md:bg-transparent rounded-[24px] md:rounded-none p-6 md:p-0">
          {children}
        </main>
      </div>
    </div>
  );
}
