import {
  Activity,
  Bug,
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
          label: "Requirement",
          href: `${root}/requirements`,
          icon: FileCheck2,
        },
        {
          id: "test-design",
          label: "Thiết kế kiểm thử",
          href: `${root}/test-design`,
          icon: TestTube2,
        },
        { id: "traceability", label: "Traceability", href: `${root}/traceability`, icon: Network },
        {
          id: "changes",
          label: "Change Intelligence",
          href: `${root}/changes`,
          icon: GitCompareArrows,
        },
        { id: "execution", label: "Execution", href: `${root}/execution`, icon: PlayCircle },
        { id: "defects", label: "Defect", href: `${root}/defects`, icon: Bug },
        { id: "knowledge", label: "Knowledge Search", href: `${root}/knowledge`, icon: Search },
        {
          id: "project-settings",
          label: "Cài đặt và audit",
          href: `${root}/settings`,
          icon: Activity,
        },
      ]
    : [];
  return [
    {
      label: "Workspace",
      items: [
        { id: "projects", label: "Dự án", href: "/qa/projects", icon: FolderKanban },
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
    .map((group) => ({ ...group, items: group.items.filter((item) => !item.requireAuth || user) }))
    .filter((group) => group.items.length > 0);
}
