"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";

interface MenuItem {
  id: string;
  label: string;
  href: string;
  requireAuth?: boolean;
  roles?: string[];
}

interface MenuGroup {
  label: string;
  items: MenuItem[];
}

export const MENU_GROUPS: MenuGroup[] = [
  {
    label: "Không gian",
    items: [
      { id: "explore", label: "Khám phá", href: "/kham-pha" },
      {
        id: "chat",
        label: "Metis",
        href: "/tro-chuyen",
        requireAuth: true,
      },
      {
        id: "message",
        label: "Tin nhắn",
        href: "/tin-nhan",
        requireAuth: true,
      },
      {
        id: "library",
        label: "Thư viện",
        href: "/thu-vien",
        requireAuth: true,
      },
    ],
  },
  {
    label: "Tài liệu",
    items: [
      {
        id: "editor",
        label: "Soạn thảo",
        href: "/soan-thao",
        roles: ["author", "admin"],
      },
      {
        id: "documents",
        label: "Tài liệu",
        href: "/tai-lieu",
        roles: ["author", "admin"],
      },
      {
        id: "collaboration",
        label: "Cộng tác",
        href: "/cong-tac",
        roles: ["author", "admin"],
      },
      {
        id: "storage",
        label: "Lưu trữ",
        href: "/luu-tru",
        roles: ["author", "admin"],
      },
      {
        id: "analytics",
        label: "Phân tích",
        href: "/phan-tich",
        roles: ["author", "admin"],
      },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      {
        id: "profile",
        label: "Hồ sơ",
        href: "/ho-so",
        requireAuth: true,
      },
      {
        id: "wallet",
        label: "Ví tiền",
        href: "/vi-tien",
        requireAuth: true,
      },
      {
        id: "settings",
        label: "Cài đặt",
        href: "/cai-dat",
        requireAuth: true,
      },
    ],
  },
  {
    label: "Quản trị",
    items: [
      {
        id: "audit",
        label: "Kiểm toán",
        href: "/kiem-toan",
        roles: ["admin"],
      },
      {
        id: "collect",
        label: "Thu thập",
        href: "/thu-thap",
        roles: ["admin"],
      },
      {
        id: "users",
        label: "Người dùng",
        href: "/nguoi-dung",
        roles: ["admin"],
      },
      {
        id: "reports",
        label: "Báo cáo",
        href: "/bao-cao",
        roles: ["admin"],
      },
      {
        id: "operations",
        label: "Vận hành",
        href: "/van-hanh",
        roles: ["admin"],
      },
    ],
  },
];

export function getAvailableMenuGroups(user: any) {
  const role = String(user?.role || "").toLowerCase();
  return MENU_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => {
      if (item.requireAuth && !user) return false;
      if (item.roles && !item.roles.includes(role)) return false;
      return true;
    }),
  })).filter((group) => group.items.length > 0);
}

export function MenuGroups({
  onNavigate,
}: {
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;
  const groups = getAvailableMenuGroups(user);

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <section key={group.label}>
          <h2 className="mb-2 px-3 text-[12px] font-medium text-[var(--ink-faint)]">
            {group.label}
          </h2>
          <div className="space-y-1">
            {group.items.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={`block min-h-10 rounded-[var(--radius-control)] px-3 py-2 text-[14px] transition-colors ${
                    active
                      ? "bg-[var(--brand-soft)] font-semibold text-[var(--brand)]"
                      : "text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

export default function Dock() {
  return (
    <aside className="fixed bottom-0 left-0 top-[var(--topbar-height)] z-30 hidden w-[var(--sidebar-width)] overflow-y-auto border-r border-[var(--border)] bg-[var(--surface-raised)] lg:block">
      <nav aria-label="Điều hướng chính" className="px-3 py-6">
        <MenuGroups />
      </nav>
    </aside>
  );
}
