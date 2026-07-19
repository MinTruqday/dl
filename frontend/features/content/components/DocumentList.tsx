import React from "react";
import { FileText, Lock, Globe, Star, MoreVertical } from "lucide-react";
import { formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";
import Link from "next/link";

interface DocumentListProps {
  layout: "grid" | "list";
  displayItems: any[];
  handleContextMenu: (e: React.MouseEvent, item: any) => void;
  isLoading: boolean;
  hasMore: boolean;
  isRefreshing: boolean;
  loaderRef: React.RefObject<HTMLDivElement>;
}

export function DocumentList({
  layout,
  displayItems,
  handleContextMenu,
  isLoading,
  hasMore,
  isRefreshing,
  loaderRef
}: DocumentListProps) {
  if (displayItems.length === 0 && !isLoading && !isRefreshing) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-20">
        <div className="w-24 h-24 bg-[#F5F5F7] rounded-full flex items-center justify-center mb-6">
          <FileText className="w-10 h-10 text-[#A1A1A6]" />
        </div>
        <p className="text-[17px] font-medium text-[#1D1D1F] mb-2">Chưa có tài liệu</p>
        <p className="text-[14px] text-[#6E6E73]">Tạo tài liệu mới để bắt đầu.</p>
      </div>
    );
  }

  return (
    <>
      {layout === "grid" ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-8">
          {displayItems.map((item) => (
            <div
              key={item._id || item.id}
              onContextMenu={(e) => handleContextMenu(e, item)}
              className="group flex flex-col bg-[#F5F5F7] hover:bg-white rounded-[18px] cursor-pointer transition-all relative border border-transparent hover:border-[#E8E8ED] hover:shadow-sm overflow-hidden"
            >
              {item.is_starred && (
                <Star className="w-4 h-4 absolute top-4 left-4 text-[#FF9500] fill-[#FF9500] z-10" />
              )}
              <Link href={`/tai-lieu/${item.slug}`} className="absolute inset-0 z-0"></Link>
              <div className="flex-1 flex items-center justify-center p-6 bg-white border-b border-[#E8E8ED]">
                <FileText className="w-12 h-12 text-[#0071E3]" />
              </div>
              <div className="p-4 bg-[#F5F5F7] group-hover:bg-white transition-colors">
                <p className="text-[14px] font-medium text-[#1D1D1F] truncate mb-1" title={item.title}>
                  {item.title}
                </p>
                <div className="flex items-center justify-between text-[12px] text-[#6E6E73]">
                  <span className="truncate max-w-[100px]">{formatRelativeTime(parseUTC(item.created_at))}</span>
                  {item.visibility === "private" ? <Lock className="w-3.5 h-3.5" /> : <Globe className="w-3.5 h-3.5" />}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleContextMenu(e, item);
                }}
                className="absolute top-2 right-2 p-1.5 opacity-0 group-hover:opacity-100 hover:bg-[#F5F5F7] rounded-full transition-all text-[#6E6E73] z-10 bg-white shadow-sm"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="w-full overflow-x-auto pb-8">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E8E8ED]">
                <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap">Tên</th>
                <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap hidden sm:table-cell">Ngày tạo</th>
                <th className="py-3 px-4 text-[13px] font-medium text-[#6E6E73] whitespace-nowrap hidden md:table-cell">Trạng thái</th>
                <th className="py-3 px-4 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {displayItems.map((item) => (
                <tr
                  key={item._id || item.id}
                  onContextMenu={(e) => handleContextMenu(e, item)}
                  className="group border-b border-[#F5F5F7] hover:bg-[#F5F5F7] transition-colors relative"
                >
                  <td className="py-3 px-4">
                    <Link href={`/tai-lieu/${item.slug}`} className="absolute inset-0 z-0"></Link>
                    <div className="flex items-center gap-3 relative z-10 pointer-events-none">
                      <div className="w-8 h-8 rounded-[10px] bg-white border border-[#E8E8ED] flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4 text-[#0071E3]" />
                      </div>
                      <span className="text-[14px] font-medium text-[#1D1D1F] truncate max-w-[150px] sm:max-w-xs md:max-w-md">
                        {item.title}
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
                    <span className={`px-2 py-1 rounded-full text-[12px] font-medium ${item.status === 'published' ? 'bg-[#34C759]/10 text-[#34C759]' : 'bg-[#FF9F0A]/10 text-[#FF9F0A]'}`}>
                      {item.status === 'published' ? 'Đã xuất bản' : 'Bản nháp'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        handleContextMenu(e, item);
                      }}
                      className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-[#E8E8ED] rounded-full transition-all text-[#6E6E73] relative z-10"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Infinite Scroll Loader */}
      {(hasMore || isRefreshing) && (
        <div ref={loaderRef} className="py-6 flex justify-center w-full">
          <div className="w-6 h-6 border-2 border-[#0071E3] border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
    </>
  );
}
