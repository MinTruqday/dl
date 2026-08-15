import {
  Bell,
  CircleHelp,
  Database,
  FileText,
  FolderOpen,
  Library,
  MessageCircle,
  PenLine,
  Search,
  Settings,
  UsersRound,
} from "lucide-react";

export type NavigationItem = {
  id: string;
  label: string;
  href: string;
  icon: typeof Search;
  requireAuth?: boolean;
  roles?: string[];
};

export type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Không gian làm việc",
    items: [
      { id: "explore", label: "Khám phá", href: "/kham-pha", icon: Search },
      {
        id: "library",
        label: "Thư viện",
        href: "/thu-vien",
        icon: Library,
        requireAuth: true,
      },
      {
        id: "chat",
        label: "Trò chuyện",
        href: "/tro-chuyen",
        icon: MessageCircle,
        requireAuth: true,
      },
    ],
  },
  {
    label: "Sáng tác",
    items: [
      {
        id: "compose",
        label: "Soạn thảo",
        href: "/soan-thao",
        icon: PenLine,
        roles: ["author", "admin"],
      },
      {
        id: "documents",
        label: "Tài liệu",
        href: "/tai-lieu",
        icon: FileText,
        roles: ["author", "admin"],
      },
      {
        id: "collaboration",
        label: "Cộng tác",
        href: "/cong-tac",
        icon: UsersRound,
        roles: ["author", "admin"],
      },
      {
        id: "storage",
        label: "Lưu trữ",
        href: "/luu-tru",
        icon: FolderOpen,
        roles: ["author", "admin"],
      },
    ],
  },
  {
    label: "Quản trị",
    items: [
      {
        id: "collection",
        label: "Thu thập",
        href: "/thu-thap",
        icon: Database,
        roles: ["admin"],
      },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      {
        id: "notifications",
        label: "Thông báo",
        href: "/thong-bao",
        icon: Bell,
        requireAuth: true,
      },
      {
        id: "settings",
        label: "Cài đặt",
        href: "/cai-dat",
        icon: Settings,
        requireAuth: true,
      },
      {
        id: "help",
        label: "Trợ giúp",
        href: "/tro-giup",
        icon: CircleHelp,
        requireAuth: true,
      },
    ],
  },
];

export function availableNavigation(groups: NavigationGroup[], user: any) {
  return groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (item.requireAuth && !user) return false;
        if (!item.roles) return true;
        return item.roles.includes(String(user?.role || "").toLowerCase());
      }),
    }))
    .filter((group) => group.items.length > 0);
}
