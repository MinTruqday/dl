"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
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
  Ticket,
  FolderOpen,
  Clock,
  CheckCircle2,
  MessageSquare,
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
          transition-all duration-300 ease-in-out group relative w-full h-14 shrink-0
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
        <div className="flex-1 overflow-y-auto py-2 scroll-smooth flex flex-col pb-20 no-scrollbar">
          <NavLink icon={Search} label="Khám phá" href="/" />
          <NavLink icon={FileText} label="Bảng tin" href="/feed" />
          <NavLink icon={Trophy} label="Vinh danh" href="/leaderboard" />
          <NavLink icon={MessageSquare} label="Tin nhắn" href="/messages" requireAuth />
          <NavLink icon={History} href="/history" label="Lịch sử" requireAuth />
          <NavLink icon={Library} href="/library" label="Thư viện" requireAuth />
          <NavLink icon={User} href="/profile" label="Hồ sơ" requireAuth />
          <NavLink icon={Bookmark} href="/collection" label="Bộ sưu tập" requireAuth />
          <NavLink icon={Wallet} href="/wallet" label="Ví" requireAuth />
          
          <NavLink
            href="/create"
            label="Sáng tác"
            icon={PenTool}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/coupon"
            label="Ưu đãi"
            icon={Ticket}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/collab"
            label="Hợp tác"
            icon={Users}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/assets"
            label="Kho lưu trữ"
            icon={FolderOpen}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/payout"
            label="Doanh thu"
            icon={Wallet}
            roles={["author", "admin"]}
          />
          
          <NavLink
            href="/my-documents"
            label="Kho tài liệu"
            icon={FileText}
            roles={["admin", "author"]}
          />
          
          <NavLink
            href="/moderation/documents"
            label="Duyệt bản thảo"
            icon={CheckCircle2}
            roles={["moderator", "admin"]}
          />
          <NavLink
            href="/moderation/logs"
            label="Nhật ký kiểm duyệt"
            icon={Clock}
            roles={["moderator", "admin"]}
          />

          <NavLink
            href="/user"
            label="Người dùng"
            icon={Users}
            roles={["admin"]}
          />
          <NavLink
            href="/applications"
            label="Đơn ứng tuyển"
            icon={UserCheck}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/reports"
            label="Báo cáo"
            icon={AlertTriangle}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/administration"
            label="Quản trị hệ thống"
            icon={Shield}
            roles={["admin"]}
          />
          
          <NavLink href="/settings" label="Cài đặt" icon={Settings} requireAuth />
        </div>
      </aside>
    </>
  );
}
