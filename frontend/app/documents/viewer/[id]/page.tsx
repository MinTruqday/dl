"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { getToken } from "../../../lib/api";
import { ToastContainer } from "../../../components/Toast";
import { Lock, FileText, AlertTriangle } from "lucide-react";

export default function DocumentViewer() {
  const { id } = useParams() as { id: string };
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  const [password, setPassword] = useState("");
  const [isLocked, setIsLocked] = useState(false);
  const [toasts, setToasts] = useState<any[]>([]);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const idMsg = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id: idMsg, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== idMsg)), 4000);
  }, []);

  useEffect(() => {
    fetchDocument();
  }, [id]);

  const fetchDocument = async (pwd?: string) => {
    setLoading(true);
    try {
      const token = getToken();
      let url = `${process.env.NEXT_PUBLIC_API_URL}/documents/${id}`;
      if (pwd) url += `?password=${encodeURIComponent(pwd)}`;

      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (res.status === 403) {
        setIsLocked(true);
        setLoading(false);
        return;
      }

      if (res.ok) {
        const data = await res.json();
        setDoc(data);
        setIsLocked(false);
      } else {
        setError("Bạn không có quyền xem tài liệu này.");
      }
    } catch (e) {
      setError("Không thể tải nội dung, vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  };

  const submitPassword = () => {
    if (!password) return showToast("Vui lòng nhập mật khẩu.", "error");
    fetchDocument(password);
  };

  if (loading) return <div className="p-10 font-bold text-zinc-500 animate-pulse flex flex-col items-center justify-center min-h-screen bg-white">
      <FileText className="w-16 h-16 mb-4 text-zinc-100" />
      Đang tải tài liệu
  </div>;
  
  if (error) return <div className="p-10 text-black font-bold flex items-center justify-center min-h-screen gap-2 bg-white">
      <AlertTriangle className="w-8 h-8" />
      {error}
  </div>;

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white p-4">
        <ToastContainer toasts={toasts} removeToast={(tId) => setToasts(prev => prev.filter(t => t.id !== tId))} />
        <div className="bg-white p-12  w-full max-w-md border border-black flex flex-col items-center text-center animate-in zoom-in slide-in-from-bottom-8 duration-300">
            <div className="w-20 h-20 bg-black text-white flex items-center justify-center  mb-8">
                <Lock className="w-10 h-10" />
            </div>
            <h2 className="text-2xl font-bold text-black mb-4 tracking-tight">Tài liệu được bảo vệ</h2>
            <p className="text-zinc-500 mb-10 text-sm font-medium leading-relaxed">Vui lòng nhập mật khẩu để truy cập nội dung này.</p>
            
            <input
                type="password"
                placeholder="Nhập mật khẩu"
                className="w-full border border-black p-4 mb-6  text-center font-bold tracking-[0.2em] focus:bg-zinc-50 outline-none transition-all placeholder:text-zinc-300"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitPassword()}
            />
            <button onClick={submitPassword} className="w-full bg-black text-white font-bold py-4  hover:bg-zinc-800 active:scale-[0.98] transition-all flex justify-center items-center gap-3 text-xs tracking-widest">
                Xác thực truy cập <Lock className="w-4 h-4" />
            </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-12 mt-10 animate-in fade-in duration-500">
      <h1 className="text-4xl font-bold mb-8 text-black leading-tight tracking-tight">{doc?.title || "Không có tiêu đề"}</h1>
      <div className="whitespace-pre-wrap bg-white p-10  border border-black text-zinc-800 leading-loose text-lg font-medium">
        {doc?.content}
      </div>
    </div>
  );
}
