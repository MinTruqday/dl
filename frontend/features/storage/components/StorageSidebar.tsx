import React from "react";
import { ChevronRight } from "lucide-react";

interface StorageSidebarProps {
  viewMode: string;
  setViewMode: (mode: string) => void;
}

export function StorageSidebar({ viewMode, setViewMode }: StorageSidebarProps) {
  const navItems = [
    { id: "files", label: "Tất cả" },
    { id: "recent", label: "Gần đây" },
    { id: "documents", label: "Tệp tin" },
    { id: "published", label: "Tài liệu" },
    { id: "folders", label: "Thư mục" },
    { id: "trash", label: "Thùng rác" },
  ];

  return (
    <aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6 z-10">
      <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
        <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
          Phân loại
        </p>
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setViewMode(item.id)}
              className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${
                viewMode === item.id
                  ? "bg-white text-[#0071E3] font-medium shadow-sm border border-[#E8E8ED]"
                  : "text-[#1D1D1F] hover:bg-[#F5F5F7]"
              }`}
            >
              <span className="truncate text-left">{item.label}</span>
              {viewMode === item.id && <ChevronRight className="w-4 h-4 shrink-0" />}
            </button>
          ))}
        </nav>
      </div>
    </aside>
  );
}
