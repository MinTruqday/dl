import React from "react";
import { ChevronRight, Grid, List, UploadCloud, FilePlus, FolderPlus, Trash2 } from "lucide-react";

interface StorageToolbarProps {
  viewMode: string;
  breadcrumbs: { id: string; name: string }[];
  handleNavigateBreadcrumb: (index: number) => void;
  layout: "grid" | "list";
  setLayout: (layout: "grid" | "list") => void;
  handleUploadClick: () => void;
  handleUploadClickDoc: () => void;
  setShowNewFolderModal: (show: boolean) => void;
  handleDeleteEmptyTrash: () => void;
}

export function StorageToolbar({
  viewMode,
  breadcrumbs,
  handleNavigateBreadcrumb,
  layout,
  setLayout,
  handleUploadClick,
  handleUploadClickDoc,
  setShowNewFolderModal,
  handleDeleteEmptyTrash
}: StorageToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h2 className="flex items-center gap-2 text-[20px] font-semibold text-[#1D1D1F]">
        {viewMode === "trash" ? (
          <span>Thùng rác</span>
        ) : viewMode === "recent" ? (
          <span>Mở gần đây</span>
        ) : viewMode === "documents" ? (
          <span>Tệp tin</span>
        ) : viewMode === "published" ? (
          <span>Tài liệu</span>
        ) : viewMode === "folders" ? (
          <span>Thư mục</span>
        ) : (
          breadcrumbs.map((crumb, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <button
                onClick={() => handleNavigateBreadcrumb(idx)}
                className={`flex items-center gap-1 transition-colors ${idx === breadcrumbs.length - 1 ? "text-[#1D1D1F]" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}
              >
                {crumb.name}
              </button>
              {idx < breadcrumbs.length - 1 && <ChevronRight className="w-4 h-4 text-[#86868B]" />}
            </div>
          ))
        )}
      </h2>

      <div className="flex items-center gap-3">
        {viewMode !== "trash" && (
          <>
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

            <div className="h-6 w-[1px] bg-[#E8E8ED]"></div>

            <button
              onClick={() => setShowNewFolderModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
            >
              <FolderPlus className="w-4 h-4" />
              <span>Thư mục mới</span>
            </button>
            <button
              onClick={handleUploadClick}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Tải tệp tin</span>
            </button>
            <button
              onClick={handleUploadClickDoc}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium bg-[#0071E3] text-white hover:bg-[#0055C6] rounded-full shadow-sm transition-colors"
            >
              <FilePlus className="w-4 h-4" />
              <span>Đăng tài liệu</span>
            </button>
          </>
        )}

        {viewMode === "trash" && (
          <button
            onClick={handleDeleteEmptyTrash}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[13px] font-medium bg-[#F5F5F7] text-red-500 hover:bg-red-50 hover:border-red-200 border border-transparent rounded-full transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Dọn sạch thùng rác</span>
          </button>
        )}
      </div>
    </div>
  );
}
