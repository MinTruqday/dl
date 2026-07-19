import React from "react";
import { ChevronRight, Filter, Search, SortAsc, SortDesc, Grid, List, Plus } from "lucide-react";

interface DocumentToolbarProps {
  currentFolder: any;
  breadcrumbs: any[];
  setCurrentFolder: (folder: any) => void;
  setBreadcrumbs: (crumbs: any[]) => void;
  setShowSearch: (show: boolean) => void;
  showSearch: boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  sortOrder: "asc" | "desc";
  setSortOrder: (order: "asc" | "desc") => void;
  layout: "grid" | "list";
  setLayout: (layout: "grid" | "list") => void;
  setShowPublishModal: (show: boolean) => void;
}

export function DocumentToolbar({
  currentFolder,
  breadcrumbs,
  setCurrentFolder,
  setBreadcrumbs,
  setShowSearch,
  showSearch,
  searchQuery,
  setSearchQuery,
  sortOrder,
  setSortOrder,
  layout,
  setLayout,
  setShowPublishModal
}: DocumentToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h2 className="flex items-center gap-2 text-[20px] font-semibold text-[#1D1D1F]">
        {!currentFolder && breadcrumbs.length === 0 ? (
          <span>Gốc</span>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setCurrentFolder(null);
                setBreadcrumbs([]);
              }}
              className="flex items-center gap-1 transition-colors hover:text-[#1D1D1F] text-[#6E6E73]"
            >
              Gốc
            </button>
            <ChevronRight className="w-5 h-5 text-[#A1A1A6]" />
            {breadcrumbs.map((crumb, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const newCrumbs = breadcrumbs.slice(0, idx + 1);
                    setBreadcrumbs(newCrumbs);
                    setCurrentFolder(crumb);
                  }}
                  className={`flex items-center gap-1 transition-colors ${idx === breadcrumbs.length - 1 ? "text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
                >
                  {crumb.name}
                </button>
                {idx < breadcrumbs.length - 1 && <ChevronRight className="w-4 h-4 text-[#86868B]" />}
              </div>
            ))}
          </div>
        )}
      </h2>

      <div className="flex items-center gap-3">
        <div className="flex items-center bg-[#F5F5F7] p-1 rounded-full">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className={`p-1.5 rounded-full transition-colors ${showSearch ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
          >
            <Search className="w-4 h-4" />
          </button>
          <button
            onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
            className="p-1.5 rounded-full transition-colors text-[#6E6E73] hover:text-[#1D1D1F]"
          >
            {sortOrder === "asc" ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
          </button>
        </div>
        
        <div className="flex items-center bg-[#F5F5F7] p-1 rounded-full">
          <button
            onClick={() => setLayout("grid")}
            className={`p-1.5 rounded-full transition-colors ${layout === "grid" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setLayout("list")}
            className={`p-1.5 rounded-full transition-colors ${layout === "list" ? "bg-white text-[#1D1D1F] shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>

        <button
          onClick={() => setShowPublishModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium bg-[#0071E3] text-white hover:bg-[#0055C6] rounded-full shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo tài liệu</span>
        </button>
      </div>
    </div>
  );
}
