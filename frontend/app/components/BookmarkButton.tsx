"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "../lib/api";
import { ToastContainer } from "./Toast";
import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";

export default function BookmarkButton({ documentId }: { documentId: string }) {
  const [isSaved, setIsSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<any[]>([]);
  const token = getToken();

  const showToast = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const checkSaved = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reading/library`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setIsSaved(data.some((d: any) => d.document_id === documentId));
      }
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
      const url = `${process.env.NEXT_PUBLIC_API_URL}/reading/library`;
      const method = isSaved ? "DELETE" : "POST";
      const body = isSaved
        ? JSON.stringify({ document_id: documentId })
        : JSON.stringify({ document_id: documentId, status: "reading" });

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body,
      });

      if (res.ok) {
        setIsSaved(!isSaved);
        showToast(isSaved ? "Đã bỏ lưu tài liệu." : "Đã lưu tài liệu thành công.", "success");
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
      <div className="flex items-center gap-2 px-6 py-3 border border-zinc-200 text-zinc-300 font-bold text-[13px] transition-all duration-300">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Đang tải</span>
      </div>
    );
  }

  return (
    <>
      <ToastContainer toasts={toasts} removeToast={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
      <button
        onClick={toggleSave}
        className={`flex items-center gap-2 px-8 py-3.5 font-bold transition-all duration-150 active:scale-[0.98] text-xs border ${
          isSaved
            ? "bg-white text-black border-zinc-200 hover:border-black hover:bg-zinc-50"
            : "bg-black text-white border-black hover:bg-zinc-800"
        }`}
      >
        {isSaved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
        <span>{isSaved ? "Bỏ lưu tài liệu" : "Lưu vào thư viện"}</span>
      </button>
    </>
  );
}
