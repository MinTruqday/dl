import React from "react";
import { PlusIcon, MessageSquare, Trash2 } from "lucide-react";
import { formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";

interface AgenticSidebarProps {
  sessions: any[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
}

export function AgenticSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}: AgenticSidebarProps) {
  return (
    <aside className="w-full lg:w-[320px] bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none flex flex-col overflow-hidden shrink-0 hidden lg:flex">
      <div className="px-6 md:px-0 pt-6 pb-4 flex items-center justify-between shrink-0">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Lịch sử</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => (window.location.href = "/nang-cap")}
            className="px-3 py-1.5 text-[13px] font-medium bg-[#0071E3] text-white rounded-full hover:bg-[#0055C6] transition-colors shadow-sm"
          >
            Nâng cấp
          </button>
          <button
            onClick={onNewSession}
            className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
            title="Cuộc trò chuyện mới"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="overflow-y-auto px-6 md:px-0 pb-6 flex flex-col gap-2 shrink custom-scrollbar">
        {sessions.length === 0 ? (
          <div className="py-12 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px]">
            <p className="text-[17px] font-medium text-[#6E6E73]">
              Chưa có dữ liệu
            </p>
          </div>
        ) : (
          sessions.map((sess) => (
            <div
              key={sess.session_id}
              onClick={() => onSelectSession(sess.session_id)}
              className={`w-full text-left p-4 rounded-[14px] transition-colors border group ${
                currentSessionId === sess.session_id
                  ? "bg-white border-[#0071E3] shadow-sm"
                  : "bg-white border-[#E8E8ED] hover:bg-[#F5F5F7]"
              } cursor-pointer`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div
                    className={`p-2 rounded-[10px] shrink-0 ${
                      currentSessionId === sess.session_id
                        ? "bg-[#0071E3]/10 text-[#0071E3]"
                        : "bg-[#F5F5F7] text-[#86868B]"
                    }`}
                  >
                    <MessageSquare className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0 flex flex-col justify-center h-9">
                    <p className={`text-[15px] truncate ${currentSessionId === sess.session_id ? "font-semibold text-[#1D1D1F]" : "font-medium text-[#1D1D1F]"}`}>
                      {sess.title || "Cuộc trò chuyện mới"}
                    </p>
                    <p className="text-[13px] text-[#86868B]">
                      {formatRelativeTime(parseUTC(sess.created_at))}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.session_id);
                  }}
                  className={`p-2 rounded-full hover:bg-red-50 text-[#86868B] hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 ${
                    currentSessionId === sess.session_id ? "opacity-100" : ""
                  }`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
