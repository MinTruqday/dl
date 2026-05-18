"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/Auth";
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

interface MenuProps {
  isOpen: boolean;
  onToggle: () => void;
  isMobileOverlay?: boolean;
  onMobileClose?: () => void;
}

export default function Menu({
  isOpen,
  onToggle,
  isMobileOverlay = false,
  onMobileClose,
}: MenuProps) {
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
            icon={Users}
            label="Cộng đồng"
            href="/cong-dong"
            requireAuth
          />
          <NavLink icon={Trophy} label="Xếp hạng" href="/xep-hang" />
          <NavLink
            icon={MessageSquare}
            label="Tin nhắn"
            href="/tin-nhan"
            requireAuth
          />
          <NavLink
            icon={Library}
            href="/thu-vien"
            label="Thư viện"
            requireAuth
          />
          <NavLink icon={User} href="/ho-so" label="Hồ sơ" requireAuth />
          <NavLink icon={Wallet} href="/vi-tien" label="Ví" requireAuth />

          <div className="mt-4 mb-2 px-6">
            <span className={`text-[10px] font-bold text-zinc-400 uppercase tracking-wider ${!isOpen && "hidden"}`}>Tác giả & Quản lý</span>
            {!isOpen && <div className="h-px w-6 mx-auto bg-zinc-200" />}
          </div>
          
          <NavLink
            href="/khoi-tao"
            label="Sáng tác"
            icon={PenTool}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/ma-giam-gia"
            label="Ưu đãi"
            icon={Ticket}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/cong-tac"
            label="Hợp tác"
            icon={Users}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/luu-tru"
            label="Kho lưu trữ"
            icon={FolderOpen}
            roles={["author", "admin"]}
          />
          <NavLink
            href="/rut-tien"
            label="Doanh thu"
            icon={Wallet}
            roles={["author", "admin"]}
          />

          <NavLink
            href="/tai-lieu"
            label="Kho tài liệu"
            icon={Files}
            roles={["admin", "author"]}
          />

          <div className="mt-4 mb-2 px-6">
            <span className={`text-[10px] font-bold text-zinc-400 uppercase tracking-wider ${!isOpen && "hidden"}`}>Quản trị</span>
            {!isOpen && <div className="h-px w-6 mx-auto bg-zinc-200" />}
          </div>

          <NavLink
            href="/nhat-ky"
            label="Nhật ký hệ thống"
            icon={Clock}
            roles={["moderator", "admin"]}
          />
          <NavLink
            href="/thu-thap"
            label="Thu thập dữ liệu"
            icon={Database}
            roles={["admin"]}
          />

          <NavLink
            href="/quan-ly-nguoi-dung"
            label="Người dùng"
            icon={Users}
            roles={["admin"]}
          />
          <NavLink
            href="/tac-gia-tiem-nang"
            label="Tác giả tiềm năng"
            icon={UserCheck}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/bao-cao"
            label="Báo cáo vi phạm"
            icon={AlertTriangle}
            roles={["admin", "moderator"]}
          />
          <NavLink
            href="/van-hanh"
            label="Quản trị hệ thống"
            icon={Shield}
            roles={["admin"]}
          />

          <div className="mt-auto pt-4 border-t border-zinc-200">
            <NavLink
              href="/cai-dat"
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
