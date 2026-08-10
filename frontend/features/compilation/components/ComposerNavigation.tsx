import RouteTabs from "@/shared/components/navigation/RouteTabs";

const items = [
  { href: "/soan-thao", label: "Tổng quan" },
  { href: "/soan-thao/ban-thao", label: "Bản thảo" },
  { href: "/soan-thao/khoi-tao", label: "Tạo mới" },
  { href: "/soan-thao/thung-rac", label: "Thùng rác" },
];

export default function ComposerNavigation() {
  return <RouteTabs items={items} label="Quản lý soạn thảo" />;
}
