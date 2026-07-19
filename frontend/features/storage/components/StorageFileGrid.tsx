import React from "react";
import { Folder, File, Star, MoreVertical } from "lucide-react";
import { formatSize, formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";

interface StorageFileGridProps {
  layout: "grid" | "list";
  displayItems: any[];
  viewMode: string;
  handleFolderClick: (folderId: string, folderName: string) => void;
  setDetailsItem: (item: any) => void;
  handleContextMenu: (e: React.MouseEvent, item: any) => void;
}

export function StorageFileGrid({
  layout,
  displayItems,
  viewMode,
  handleFolderClick,
  setDetailsItem,
  handleContextMenu
}: StorageFileGridProps) {
  if (displayItems.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-20">
        <div className="w-24 h-24 bg-[#F5F5F7] rounded-full flex items-center justify-center mb-6">
          <Folder className="w-10 h-10 text-[#A1A1A6]" />
        </div>
        <p className="text-[17px] font-medium text-[#1D1D1F] mb-2">Thư mục trống</p>
        <p className="text-[14px] text-[#6E6E73]">Chưa có dữ liệu nào ở đây.</p>
      </div>
    );
  }

  if (layout === "grid") {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-8">
        {displayItems.map((item) => (
          <div
            key={item._id || item.id}
            onContextMenu={(e) => handleContextMenu(e, item)}
            onClick={() => {
              if (item.is_folder) handleFolderClick(item._id || item.id, item.name);
              else setDetailsItem(item);
            }}
            className="group flex flex-col p-4 bg-[#F5F5F7] hover:bg-[#E8E8ED] rounded-[18px] cursor-pointer transition-colors relative border border-transparent hover:border-[#D2D2D7]"
          >
            {item.is_starred && (
              <Star className="w-4 h-4 absolute top-4 left-4 text-[#FF9500] fill-[#FF9500]" />
            )}
            <div className="flex-1 flex items-center justify-center py-6">
              {item.is_folder ? (
                <Folder className="w-12 h-12 text-[#0071E3]" />
              ) : viewMode === "published" ? (
                <File className="w-12 h-12 text-[#34C759]" />
              ) : (
                <File className="w-12 h-12 text-[#6E6E73]" />
              )}
            </div>
            <div className="mt-2 text-center w-full">
              <p className="text-[14px] font-medium text-[#1D1D1F] truncate px-2">
                {item.name || item.title}
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleContextMenu(e, item);
              }}
              className="absolute top-2 right-2 p-1.5 opacity-0 group-hover:opacity-100 hover:bg-[#D2D2D7] rounded-full transition-all text-[#6E6E73]"
            >
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto pb-8">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-[#E8E8ED]">
            <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap">Tên</th>
            <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap hidden sm:table-cell">Ngày tạo</th>
            <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap hidden md:table-cell">Kích thước</th>
            <th className="py-3 px-4 w-10"></th>
          </tr>
        </thead>
        <tbody>
          {displayItems.map((item) => (
            <tr
              key={item._id || item.id}
              onClick={() => {
                if (item.is_folder) handleFolderClick(item._id || item.id, item.name);
                else setDetailsItem(item);
              }}
              onContextMenu={(e) => handleContextMenu(e, item)}
              className="group border-b border-[#F5F5F7] hover:bg-[#F5F5F7] transition-colors cursor-pointer"
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-[10px] bg-white border border-[#E8E8ED] flex items-center justify-center shrink-0">
                    {item.is_folder ? (
                      <Folder className="w-4 h-4 text-[#0071E3]" />
                    ) : viewMode === "published" ? (
                      <File className="w-4 h-4 text-[#34C759]" />
                    ) : (
                      <File className="w-4 h-4 text-[#6E6E73]" />
                    )}
                  </div>
                  <span className="text-[14px] font-medium text-[#1D1D1F] truncate max-w-[150px] sm:max-w-xs md:max-w-md">
                    {item.name || item.title}
                  </span>
                  {item.is_starred && (
                    <Star className="w-3.5 h-3.5 text-[#FF9500] fill-[#FF9500] shrink-0" />
                  )}
                </div>
              </td>
              <td className="py-3 px-4 text-[13px] text-[#6E6E73] whitespace-nowrap hidden sm:table-cell">
                {formatRelativeTime(parseUTC(item.created_at))}
              </td>
              <td className="py-3 px-4 text-[13px] text-[#6E6E73] whitespace-nowrap hidden md:table-cell">
                {item.is_folder ? "--" : formatSize(item.size || 0)}
              </td>
              <td className="py-3 px-4 text-right">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleContextMenu(e, item);
                  }}
                  className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-[#E8E8ED] rounded-full transition-all text-[#6E6E73]"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
