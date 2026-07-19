import React from "react";
import { X, Folder, File } from "lucide-react";
import { formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";

interface StorageDetailsProps {
  detailsItem: any;
  setDetailsItem: (item: any) => void;
  viewMode: string;
}

export function StorageDetails({ detailsItem, setDetailsItem, viewMode }: StorageDetailsProps) {
  if (!detailsItem) return null;

  return (
    <aside className="w-full h-full min-h-0 bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] flex flex-col gap-6 overflow-hidden relative">
      <div className="p-6 flex justify-between items-center bg-white sticky top-0 z-10 border-b border-[#E8E8ED]">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
          Chi tiết
        </h2>
        <button
          onClick={() => setDetailsItem(null)}
          className="w-8 h-8 flex items-center justify-center bg-[#F5F5F7] rounded-full text-[#6E6E73] hover:text-[#1D1D1F] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-6 w-full md:w-[320px]">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 bg-white flex items-center justify-center rounded-[20px] mb-4 shadow-sm border border-[#E8E8ED]">
              {detailsItem?.is_folder ? (
                <Folder className="w-12 h-12 text-[#0071E3]" />
              ) : (
                <File className="w-12 h-12 text-[#6E6E73]" />
              )}
            </div>
            <p className="text-[14px] font-medium text-[#1D1D1F] mb-4 text-center max-w-full break-words">
              {detailsItem?.name || detailsItem?.title}
            </p>
          </div>
          <div className="bg-white rounded-[18px] p-5 space-y-3 shadow-sm border border-[#E8E8ED]">
            <div className="flex justify-between items-center text-[14px]">
              <span className="text-[#6E6E73]">Loại</span>
              <span className="font-medium">
                {viewMode === "published"
                  ? "Tác phẩm"
                  : detailsItem?.is_folder
                  ? "Thư mục"
                  : detailsItem?.mime_type || "Tệp tin"}
              </span>
            </div>
            {viewMode === "published" ? (
              <>
                <div className="flex justify-between items-center text-[14px]">
                  <span className="text-[#6E6E73]">Thể loại</span>
                  <span className="font-medium">
                    {detailsItem?.category || "Chưa phân loại"}
                  </span>
                </div>
                <div className="flex justify-between items-center text-[14px]">
                  <span className="text-[#6E6E73]">Giá bán</span>
                  <span className="font-medium text-[#0071E3] font-mono">
                    {detailsItem?.price_dl || 0} dl
                  </span>
                </div>
              </>
            ) : (
              <div className="flex justify-between items-center text-[14px]">
                <span className="text-[#6E6E73]">Kích thước</span>
                <span className="font-medium">
                  {detailsItem?.is_folder
                    ? "--"
                    : detailsItem?.size
                    ? `${(detailsItem.size / 1024 / 1024).toFixed(2)} MB`
                    : "Chưa xác định"}
                </span>
              </div>
            )}
            <div className="flex justify-between items-center text-[14px]">
              <span className="text-[#6E6E73]">Tạo lúc</span>
              <span className="font-medium">
                {formatRelativeTime(parseUTC(detailsItem?.created_at || new Date().toISOString()))}
              </span>
            </div>
          </div>
          
          {detailsItem?.description && (
             <div className="bg-white rounded-[18px] p-5 shadow-sm border border-[#E8E8ED]">
                <h4 className="text-[14px] text-[#6E6E73] mb-2 font-medium">Mô tả</h4>
                <p className="text-[14px] text-[#1D1D1F] leading-relaxed whitespace-pre-wrap">{detailsItem.description}</p>
             </div>
          )}
      </div>
    </aside>
  );
}
