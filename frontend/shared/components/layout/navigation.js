import {
  Activity,
  BrainCircuit,
  Bug,
  BarChart3,
  FileCheck2,
  FolderKanban,
  GitCompareArrows,
  LayoutDashboard,
  Network,
  PlayCircle,
  Search,
  Settings,
  TestTube2,
} from "lucide-react";

export function projectIdFromPath(pathname) {
  const match = pathname.match(/^\/qa\/projects\/([^/]+)/);
  return match?.[1] || "";
}

export function navigationGroupsFor(pathname) {
  const projectId = projectIdFromPath(pathname);
  const root = projectId ? `/qa/projects/${projectId}` : "";
  const projectItems = projectId
    ? [
        { id: "dashboard", label: "Tổng quan", href: root, icon: LayoutDashboard },
        {
          id: "requirements",
          label: "Yêu cầu",
          href: `${root}/requirements`,
          icon: FileCheck2,
        },
        {
          id: "test-design",
          label: "Thiết kế kiểm thử",
          href: `${root}/test-design`,
          icon: TestTube2,
        },
        { id: "traceability", label: "Truy vết", href: `${root}/traceability`, icon: Network },
        {
          id: "changes",
          label: "Phân tích thay đổi",
          href: `${root}/changes`,
          icon: GitCompareArrows,
        },
        {
          id: "execution",
          label: "Thực thi kiểm thử",
          href: `${root}/execution`,
          icon: PlayCircle,
        },
        {
          id: "ai-review",
          label: "Rà soát đề xuất AI",
          href: `${root}/ai-review`,
          icon: BrainCircuit,
        },
        { id: "defects", label: "Lỗi", href: `${root}/defects`, icon: Bug },
        {
          id: "reports",
          label: "Báo cáo",
          href: `${root}/reports`,
          icon: BarChart3,
        },
        { id: "knowledge", label: "Kho tri thức", href: `${root}/knowledge`, icon: Search },
        {
          id: "project-settings",
          label: "Cài đặt và nhật ký",
          href: `${root}/settings`,
          icon: Activity,
        },
      ]
    : [];
  return [
    {
      label: "Không gian làm việc",
      items: [
        { id: "projects", label: "Dự án", href: "/qa/projects", icon: FolderKanban },
        { id: "operations", label: "Vận hành nền tảng", href: "/qa/operations", icon: Activity, requireAdmin: true },
        ...projectItems,
      ],
    },
    {
      label: "Tài khoản",
      items: [
        {
          id: "account-settings",
          label: "Tài khoản",
          href: "/cai-dat",
          icon: Settings,
          requireAuth: true,
        },
      ],
    },
  ];
}

export function availableNavigation(groups, user) {
  return groups
    .map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => (!item.requireAuth || user) && (!item.requireAdmin || user?.system_role === "ADMIN"),
      ),
    }))
    .filter((group) => group.items.length > 0);
}
