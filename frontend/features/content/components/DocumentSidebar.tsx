import React from "react";
import { ChevronRight } from "lucide-react";

interface DocumentSidebarProps {
  viewMode: string;
  setViewMode: (mode: string) => void;
  setFilterStar: (star: boolean) => void;
  filterFormat: string;
  setFilterFormat: (format: string) => void;
}

export function DocumentSidebar({ viewMode, setViewMode, setFilterStar, filterFormat, setFilterFormat }: DocumentSidebarProps) {
  return (
    <aside className="w-full md:w-[240px] shrink-0 space-y-6 sticky top-0 h-fit mb-6 md:mb-0 md:mr-6">
      <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
        <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
          Phân loại
        </p>
        <nav className="flex flex-col gap-1.5">
          <button
            onClick={() => { setViewMode("list"); setFilterStar(false); setFilterFormat("all"); }}
            className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${viewMode === "list" ? "bg-white text-[#0071E3] font-medium shadow-sm border border-[#E8E8ED]" : "text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}
          >
            <span className="truncate text-left">Tất cả tài liệu</span>
            {viewMode === "list" && <ChevronRight className="w-4 h-4 shrink-0" />}
          </button>
        </nav>
      </div>

      <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 space-y-2">
        <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
          Lọc định dạng
        </p>
        <div className="relative">
          <select
            value={filterFormat}
            onChange={(e) => setFilterFormat(e.target.value)}
            className="w-full h-[44px] bg-[#F5F5F7] md:bg-white px-4 text-[14px] font-medium focus:outline-none focus:border-[#0071E3] appearance-none rounded-[10px] border border-[#E8E8ED] focus:bg-white transition-colors"
          >
            <option value="all">Mọi định dạng</option>
            <option value="pdf">PDF</option>
            <option value="docx">Word</option>
            <option value="xlsx">Excel</option>
            <option value="pptx">PowerPoint</option>
            <option value="zip">ZIP</option>
          </select>
          <ChevronRight className="w-5 h-5 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none rotate-90 text-[#6E6E73]" />
        </div>
      </div>
    </aside>
  );
}
