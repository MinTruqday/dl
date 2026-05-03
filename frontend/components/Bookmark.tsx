"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "@/services/auth.service";
import {
  getLibraryAPI,
  addToLibraryAPI,
  removeFromLibraryAPI,
} from "@/services/read.service";
import { ToastContainer } from "./Toast";
import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";

export default function Bookmark({ documentId }: { documentId: string }) {
  const [isSaved, setIsSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<any[]>([]);
  const token = getToken();

  const showToast = useCallback(
    (message: string, type: "success" | "error" | "info" = "info") => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(
        () => setToasts((prev) => prev.filter((t) => t.id !== id)),
        4000,
      );
    },
    [],
  );

  const checkSaved = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const data = await getLibraryAPI();
      setIsSaved(data.some((d: any) => d.document_id === documentId));
    } catch (err: any) {
      console.error("Lỗi kiểm tra bookmark:", err);
    } finally {
      setLoading(false);
    }
  }, [documentId, token]);

  useEffect(() => {
    checkSaved();
  }, [checkSaved]);

  const toggleSave = async () => {
    if (!token) {
      showToast("Vui lòng đăng nhập để lưu tài liệu.", "error");
      return;
    }

    try {
      const success = isSaved
        ? await removeFromLibraryAPI(documentId)
        : await addToLibraryAPI(documentId);

      if (success) {
        setIsSaved(!isSaved);
        showToast(
          isSaved ? "Đã bỏ lưu tài liệu." : "Đã lưu tài liệu thành công.",
          "success",
        );
      } else {
        showToast("Đã xảy ra lỗi khi cập nhật thư viện.", "error");
      }
    } catch (error: any) {
      console.error("Lỗi cập nhật thư viện:", error);
      showToast("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau", "error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-6 py-3 border border-zinc-200 text-zinc-300 font-bold text-[13px] ">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Đang tải</span>
      </div>
    );
  }

  return (
    <>
      <ToastContainer
        toasts={toasts}
        removeToast={(id) =>
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }
      />
      <button
        onClick={toggleSave}
        className={`flex items-center gap-2 px-8 py-3.5 font-bold active:scale-[0.98] text-xs border ${
          isSaved
            ? "bg-white text-black border-zinc-200 "
            : "bg-black text-white border-black "
        }`}
      >
        {isSaved ? (
          <BookmarkCheck className="w-4 h-4" />
        ) : (
          <Bookmark className="w-4 h-4" />
        )}
        <span>{isSaved ? "Bỏ lưu tài liệu" : "Lưu vào thư viện"}</span>
      </button>
    </>
  );
}
