"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  Compass,
  LayoutGrid,
  Library,
  BookMarked,
  Trophy,
  User,
  Wallet,
  History,
  Settings,
  ShieldCheck,
  PenTool,
  Shield,
} from "lucide-react";

export default function Sidebar({
  isOpen,
  onToggle,
  isMobileOverlay = false,
  onMobileClose,
}: {
  isOpen: boolean;
  onToggle: () => void;
  isMobileOverlay?: boolean;
  onMobileClose?: () => void;
}) {
  const pathname = usePathname();
  const { user } = useAuth() as any;

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  const NavLink = ({
    href,
    label,
    icon: Icon,
    roles,
    requireAuth = false,
  }: {
    href: string;
    label: string;
    icon: React.ElementType;
    roles?: string[];
    requireAuth?: boolean;
  }) => {
    if (requireAuth && !user) return null;

    if (roles) {
      const userRole = (user?.role || "").toLowerCase();
      const normalizedRoles = roles.map(r => r.toLowerCase());
      if (!normalizedRoles.includes(userRole)) return null;
    }

    const active = isActive(href);

    return (
      <Link
        href={href}
        onClick={isMobileOverlay ? onMobileClose : undefined}
        title={!isOpen ? label : undefined}
        className={`
          flex items-center text-[13px] font-bold tracking-tight
          transition-all duration-300 ease-in-out group relative w-full h-14
          ${isOpen ? "px-6 gap-4" : "px-0 justify-center"}
          ${active
            ? "bg-black text-white"
            : "text-zinc-500 hover:bg-zinc-50 hover:text-black"
          }
        `}
      >
        <div className="flex items-center justify-center shrink-0 w-6">
          <Icon
            className={`w-[18px] h-[18px] transition-all duration-300 ${active ? "text-white" : "text-zinc-400 group-hover:text-black"
              }`}
          />
        </div>
        <span
          className={`
            whitespace-nowrap overflow-hidden transition-all duration-500 ease-in-out
            ${isOpen ? "opacity-100 max-w-[180px] translate-x-0" : "opacity-0 max-w-0 -translate-x-4"}
          `}
        >
          {label}
        </span>

        {!isOpen && !isMobileOverlay && (
          <span className="absolute left-full ml-2 px-3 py-2 bg-black text-white text-[13px] font-bold tracking-widest whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-200 z-50 transform translate-x-2 group-hover:translate-x-0">
            {label}
          </span>
        )}
      </Link>
    );
  };

  return (
    <>
      {isMobileOverlay && isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden animate-in fade-in duration-200"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-[var(--navbar-height)] h-[calc(100dvh-var(--navbar-height))]
          bg-white border-r border-zinc-100 transition-all duration-300 ease-in-out z-40
          flex flex-col overflow-hidden
          ${isOpen ? "w-[var(--sidebar-width-expanded)]" : "w-[var(--sidebar-width-collapsed)]"}
        `}
      >
        <div className="flex-1 overflow-y-auto py-2 scroll-smooth flex flex-col hide-scrollbar">
          <NavLink href="/" label="Khám phá" icon={Compass} />
          <NavLink href="/feed" label="Bảng tin" icon={LayoutGrid} />
          <NavLink href="/leaderboard" label="Vinh danh" icon={Trophy} />

          <NavLink href="/collections" label="Bộ sưu tập" icon={BookMarked} requireAuth />
          <NavLink href="/history" label="Lịch sử đọc" icon={History} requireAuth />
          <NavLink href="/library" label="Kệ sách" icon={Library} requireAuth />

          <NavLink href="/profile" label="Hồ sơ" icon={User} requireAuth />
          <NavLink href="/wallet" label="Ví điện tử" icon={Wallet} requireAuth />

          <NavLink
            href="/studio/dashboard"
            label="Tác giả"
            icon={PenTool}
            roles={["author", "admin"]}
          />

          <NavLink
            href="/moderator"
            label="Điều phối"
            icon={Shield}
            roles={["moderator", "admin"]}
          />

          <NavLink
            href="/admin"
            label="Quản trị"
            icon={ShieldCheck}
            roles={["admin"]}
          />

          <NavLink href="/settings" label="Cài đặt" icon={Settings} requireAuth />
        </div>
      </aside>
    </>
  );
}
