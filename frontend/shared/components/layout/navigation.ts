import {
  Activity,
  BarChart3,
  BookOpen,
  ClipboardList,
  Database,
  FileText,
  GraduationCap,
  LayoutDashboard,
  PenLine,
  Settings,
  Shield,
} from "lucide-react";

export type NavigationItem = {
  id: string;
  label: string;
  href: string;
  icon: typeof LayoutDashboard;
  requireAuth?: boolean;
  roles?: string[];
  personas?: string[];
};

export type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Giáo viên",
    items: [
      { id: "teacher-dashboard", label: "Tổng quan", href: "/giao-vien", icon: LayoutDashboard, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "assessments", label: "Bài đánh giá", href: "/giao-vien/de", icon: ClipboardList, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "composer", label: "Soạn đề", href: "/giao-vien/de/soan-thao", icon: PenLine, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "question-bank", label: "Ngân hàng câu hỏi", href: "/giao-vien/cau-hoi", icon: BookOpen, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "review-queue", label: "Chờ rà soát", href: "/giao-vien/cau-hoi/ra-soat", icon: Shield, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "materials", label: "Tài liệu của tôi", href: "/giao-vien/tai-lieu", icon: FileText, roles: ["author", "admin"], personas: ["teacher"] },
      { id: "insights", label: "Hiệu chỉnh", href: "/giao-vien/hieu-chinh", icon: BarChart3, roles: ["author", "admin"], personas: ["teacher"] },
    ],
  },
  {
    label: "Học sinh",
    items: [
      { id: "student-dashboard", label: "Năng lực", href: "/hoc-sinh", icon: GraduationCap, requireAuth: true, personas: ["student"] },
      { id: "assigned", label: "Bài được giao", href: "/hoc-sinh/bai-duoc-giao", icon: ClipboardList, requireAuth: true, personas: ["student"] },
      { id: "history", label: "Lịch sử", href: "/hoc-sinh/lich-su", icon: Activity, requireAuth: true, personas: ["student"] },
    ],
  },
  {
    label: "Quản trị",
    items: [
      { id: "curriculum", label: "Chương trình học", href: "/quan-tri/chuong-trinh", icon: Database, roles: ["admin"] },
      { id: "operations", label: "Vận hành mô hình", href: "/quan-tri/van-hanh", icon: Activity, roles: ["admin"] },
      { id: "security", label: "Nhật ký bảo mật", href: "/quan-tri/bao-mat", icon: Shield, roles: ["admin"] },
    ],
  },
  {
    label: "Tài khoản",
    items: [
      { id: "settings", label: "Cài đặt", href: "/cai-dat", icon: Settings, requireAuth: true },
      { id: "persona-settings", label: "Vai trò sử dụng", href: "/cai-dat/vai-tro", icon: GraduationCap, requireAuth: true },
    ],
  },
];

export function availableNavigation(groups: NavigationGroup[], user: any, personas: string[] = []) {
  return groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => {
        if (item.requireAuth && !user) return false;
        if (item.roles && !item.roles.includes(String(user?.role || "").toLowerCase())) return false;
        if (!item.personas || !personas.length || String(user?.role || "").toLowerCase() === "admin") return true;
        return item.personas.some((persona) => personas.includes(persona));
      }),
    }))
    .filter((group) => group.items.length > 0);
}
