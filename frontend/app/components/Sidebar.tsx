"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  Search,
  FileText,
  Library,
  Bookmark,
  Trophy,
  User,
  Wallet,
  History,
  Settings,
  ShieldCheck,
  PenTool,
  Shield,
  UserCheck,
  AlertTriangle,
  Users,
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
          active:scale-95
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
            whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out font-sans
            ${isOpen ? "opacity-100 max-w-[180px] translate-x-0" : "opacity-0 max-w-0 -translate-x-4"}
          `}
        >
          {label}
        </span>

        {!isOpen && !isMobileOverlay && (
          <span className="absolute left-full ml-2 px-3 py-2 bg-black text-white text-[13px] font-bold whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-150 z-50 transform translate-x-2 group-hover:translate-x-0 border border-white/20 rounded-sm">
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
          className="fixed inset-0 bg-black/40 z-30 md:hidden animate-in fade-in duration-300"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-[var(--navbar-height)] h-[calc(100dvh-var(--navbar-height))]
          bg-white border-r border-zinc-100 transition-all duration-300 ease-in-out z-40
          flex flex-col overflow-hidden font-sans
          ${isOpen ? "w-[var(--sidebar-width-expanded)]" : "w-[var(--sidebar-width-collapsed)]"}
        `}
      >
        <div className="flex-1 overflow-y-auto py-2 scroll-smooth flex flex-col no-scrollbar">
          {[
            { icon: Search, label: "Khám phá", href: "/" },
            { icon: FileText, label: "Bảng tin", href: "/feed" },
            { icon: Trophy, label: "Vinh danh", href: "/leaderboard" },
          ].map((item) => (
            <NavLink key={item.href} {...item} />
          ))}

          <NavLink href="/collections" label="Bộ sưu tập" icon={Bookmark} requireAuth />
          <NavLink href="/history" label="Lịch sử đọc" icon={History} requireAuth />
          <NavLink href="/library" label="Thư viện cá nhân" icon={Library} requireAuth />

          <NavLink href="/profile" label="Hồ sơ" icon={User} requireAuth />
          <NavLink href="/wallet" label="Ví điện tử" icon={Wallet} requireAuth />


          {/* Author & Management - Spacing mt-10 */}
          <div className="mt-10 border-t border-zinc-50 pt-4">
            <NavLink
              href="/studio/dashboard"
              label="Bảng điều khiển"
              icon={User}
              roles={["author", "admin"]}
            />
            <NavLink
              href="/studio/create"
              label="Sáng tác"
              icon={PenTool}
              roles={["author", "admin"]}
            />
            <NavLink
              href="/studio/payouts"
              label="Doanh thu"
              icon={Wallet}
              roles={["author", "admin"]}
            />
          </div>

          <NavLink
            href="/documents-management"
            label="Kho tài liệu"
            icon={FileText}
            roles={["admin", "author"]}
          />

          <NavLink
            href="/moderator"
            label="Kiểm duyệt viên"
            icon={Shield}
            roles={["moderator", "admin"]}
          />

          <NavLink
            href="/admin/users"
            label="Quản lý người dùng"
            icon={Users}
            roles={["admin"]}
          />
          <NavLink
            href="/admin/applications"
            label="Đơn ứng tuyển"
            icon={UserCheck}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/admin/reports"
            label="Báo cáo vi phạm"
            icon={AlertTriangle}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/admin/config"
            label="Cấu hình hệ thống"
            icon={Settings}
            roles={["admin"]}
          />

          <NavLink href="/settings" label="Cài đặt" icon={Settings} requireAuth />
        </div>
      </aside>
    </>
  );
}
