'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/app/contexts/AuthContext';
import { Home, MessageSquare, Library, Files, PenTool, Trophy, Wallet, BarChart3, ShieldCheck } from 'lucide-react';
import { cn } from '../../lib/utils';

const NAV_ITEMS = [
  { href: '/', label: 'Trang chủ', icon: Home, roles: ['reader', 'author', 'moderator', 'admin'] },
  { href: '/feed', label: 'Bảng tin', icon: MessageSquare, roles: ['reader', 'author', 'moderator', 'admin'] },
  { href: '/library', label: 'Thư viện', icon: Library, roles: ['reader', 'author', 'moderator', 'admin'] },
  { href: '/wallet', label: 'Ví', icon: Wallet, roles: ['reader', 'author', 'moderator', 'admin'] },
  { href: '/studio', label: 'Studio', icon: PenTool, roles: ['author', 'admin'] },
  { href: '/analytics', label: 'Thống kê', icon: BarChart3, roles: ['author', 'admin'] },
  { href: '/moderation', label: 'Duyệt bài', icon: ShieldCheck, roles: ['moderator', 'admin'] },
  { href: '/leaderboard', label: 'Bảng xếp hạng', icon: Trophy, roles: ['reader', 'author', 'moderator', 'admin'] },
];

export default function SideNavigation() {
  const { user } = useAuth();
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border bg-white h-full shrink-0 hidden md:flex flex-col py-4 overflow-y-auto">
      <div className="px-3 flex flex-col gap-1">
        {NAV_ITEMS.filter(item => {
            const userRole = user?.role || 'guest';
            return item.roles.includes(userRole);
          }).map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-sm px-3 py-2 text-sm transition-all",
                isActive
                  ? "bg-zinc-100 text-zinc-900 font-semibold"
                  : "text-zinc-600 font-medium hover:text-zinc-900 hover:bg-zinc-100"
              )}
            >
              <Icon 
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors", 
                  isActive ? "text-zinc-900" : "text-zinc-400 group-hover:text-zinc-900"
                )} 
              />
              {item.label}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
