"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  Search,
  FileText,
  Library,
  Trophy,
  User,
  Wallet,
  Settings,
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
  Database,
  LayoutDashboard,
  Files,
} from "lucide-react";

export default function Menu({
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
      const normalizedRoles = roles.map((r) => r.toLowerCase());
      if (!normalizedRoles.includes(userRole)) return null;
    }

    const active = isActive(href);

    return (
      <Link
        href={href}
        onClick={isMobileOverlay ? onMobileClose : undefined}
        title={!isOpen ? label : undefined}
        className={`flex items-center text-[13px] tracking-tight transition-colors group relative w-full h-12 shrink-0 rounded-none ${
          isOpen ? "px-6 gap-4" : "px-0 justify-center"
        } ${
          active
            ? "font-semibold text-black border-l-2 border-black bg-zinc-50"
            : "font-medium text-zinc-500 border-l-2 border-transparent"
        }`}
      >
        <div className="flex items-center justify-center shrink-0 w-6">
          <Icon
            className={`w-[18px] h-[18px] ${
              active
                ? "text-black"
                : "text-zinc-400 transition-colors"
            }`}
          />
        </div>
        <span
          className={`whitespace-nowrap overflow-hidden transition-all duration-200 font-sans ${
            isOpen ? "opacity-100 max-w-[180px]" : "opacity-0 max-w-0"
          }`}
        >
          {label}
        </span>


      </Link>
    );
  };

  return (
    <>
      {isMobileOverlay && isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-[var(--navbar-height)] h-[calc(100dvh-var(--navbar-height))]
          bg-white border-r border-zinc-200 transition-all duration-200 z-40
          flex flex-col overflow-hidden font-sans
          ${isOpen ? "w-[var(--sidebar-width-expanded)]" : "w-[var(--sidebar-width-collapsed)]"}
        `}
      >
        <div className="flex-1 overflow-y-auto py-4 scroll-smooth flex flex-col pb-20 no-scrollbar">
          <NavLink icon={Search} label="Khám phá" href="/" />
          <NavLink
            icon={LayoutDashboard}
            label="Bảng tin"
            href="/feed"
            roles={["reader", "author", "admin"]}
          />
          <NavLink icon={Trophy} label="Xếp hạng" href="/rank" />
          <NavLink
            icon={MessageSquare}
            label="Tin nhắn"
            href="/messages"
            requireAuth
          />
          <NavLink
            icon={Library}
            href="/library"
            label="Thư viện"
            requireAuth
          />
          <NavLink icon={User} href="/profile" label="Hồ sơ" requireAuth />
          <NavLink icon={Wallet} href="/wallet" label="Ví" requireAuth />

          <div className="mt-4 mb-2 px-6">
            <span className={`text-[10px] font-bold text-zinc-400 uppercase tracking-wider ${!isOpen && "hidden"}`}>Tác giả & Quản lý</span>
            {!isOpen && <div className="h-px w-6 mx-auto bg-zinc-200" />}
          </div>
          
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
            href="/documents"
            label="Kho tài liệu"
            icon={Files}
            roles={["admin", "author"]}
          />

          <div className="mt-4 mb-2 px-6">
            <span className={`text-[10px] font-bold text-zinc-400 uppercase tracking-wider ${!isOpen && "hidden"}`}>Quản trị</span>
            {!isOpen && <div className="h-px w-6 mx-auto bg-zinc-200" />}
          </div>

          <NavLink
            href="/draft"
            label="Duyệt bản thảo"
            icon={CheckCircle2}
            roles={["moderator", "admin"]}
          />
          <NavLink
            href="/logs"
            label="Nhật ký hệ thống"
            icon={Clock}
            roles={["moderator", "admin"]}
          />
          <NavLink
            href="/collector"
            label="Thu thập dữ liệu"
            icon={Database}
            roles={["admin"]}
          />

          <NavLink
            href="/user"
            label="Người dùng"
            icon={Users}
            roles={["admin"]}
          />
          <NavLink
            href="/applications"
            label="Đăng ký tác giả"
            icon={UserCheck}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/reports"
            label="Báo cáo vi phạm"
            icon={AlertTriangle}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/operation"
            label="Quản trị hệ thống"
            icon={Shield}
            roles={["admin"]}
          />

          <div className="mt-auto pt-4 border-t border-zinc-200">
            <NavLink
              href="/settings"
              label="Cài đặt"
              icon={Settings}
              requireAuth
            />
          </div>
        </div>
      </aside>
    </>
  );
}
