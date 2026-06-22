"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDocumentAPI } from "@/features/content/services/document_metadata.service";
import { Loader2, BookOpen, PenTool, Globe, Lock, Code, FileText, ArrowRight } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import { useAuth } from "@/features/auth/contexts/AuthContext";

export default function CreateDocumentPage() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [contentFormat, setContentFormat] = useState("json");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setPublisherName(user.role === "admin" ? "DocLib" : user.full_name || "");
    }
  }, [user]);

  const slugify = (text: string) => {
    return text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[đĐ]/g, "d")
      .replace(/[^a-z0-9]/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await createDocumentAPI({
        title,
        slug: `${slugify(title)}-${Date.now()}`,
        description,
        publisher_name: publisherName,
        visibility,
        content_format: contentFormat,
        status: "draft",
      });
      if (res) {
        showToast("Khởi tạo tác phẩm thành công.", "success");
        setTimeout(() => {
          router.push(
            `/compose?tai-lieu=${res.data?.id || res.data?._id || res.id || res._id}`,
          );
        }, 1000);
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi khởi tạo tài liệu.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleCreate} className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0">
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
          Thông tin sơ bộ
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Thiết lập cấu trúc cơ bản cho tác phẩm mới
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
              Tiêu đề tác phẩm <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input
                required
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Nhập tiêu đề tác phẩm..."
                className="w-full h-11 pl-10 pr-4 border border-zinc-200 bg-zinc-50 text-sm font-bold text-zinc-900 focus:outline-none focus:border-zinc-400 focus:bg-white rounded-2xl transition-all duration-200 shadow-sm"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
              Người đăng / Nhà xuất bản
            </label>
            <div className="relative">
              <PenTool className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input
                readOnly={user?.role === "admin"}
                type="text"
                value={publisherName}
                onChange={(e) => setPublisherName(e.target.value)}
                className={`w-full h-11 pl-10 pr-4 border border-zinc-200 bg-zinc-50 text-sm font-bold text-zinc-900 focus:outline-none focus:border-zinc-400 focus:bg-white rounded-2xl transition-all duration-200 shadow-sm ${user?.role === "admin" ? "opacity-60 cursor-not-allowed bg-zinc-100" : ""}`}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block">
              Tóm tắt nội dung (Tùy chọn)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả ngắn gọn về nội dung tác phẩm..."
              className="w-full min-h-[120px] p-4 border border-zinc-200 bg-zinc-50 text-sm font-medium text-zinc-900 focus:outline-none focus:border-zinc-400 focus:bg-white resize-none rounded-2xl transition-all duration-200 shadow-sm"
            />
          </div>
        </div>

        <div className="space-y-4">
          <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block border-b border-zinc-100 pb-2">
            Cấu hình quyền truy cập
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                id: "public",
                label: "Công khai",
                desc: "Mọi độc giả đều có thể tiếp cận tác phẩm của bạn.",
                icon: Globe,
              },
              {
                id: "private",
                label: "Riêng tư",
                desc: "Chỉ bạn hoặc cộng tác viên được mời mới có thể xem.",
                icon: Lock,
              },
            ].map((opt) => {
              const Icon = opt.icon;
              const isSelected = visibility === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setVisibility(opt.id)}
                  className={`p-5 border text-left flex items-start gap-4 rounded-3xl transition-all duration-200 group ${isSelected ? "border-black bg-zinc-50 shadow-sm" : "bg-white border-zinc-200 hover:border-zinc-300 hover:shadow-sm"}`}
                >
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 transition-colors ${isSelected ? "bg-black text-white" : "bg-zinc-50 text-zinc-400 border border-zinc-100 group-hover:text-zinc-600"}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="space-y-1.5 pt-0.5">
                    <p className={`text-sm font-bold ${isSelected ? "text-zinc-900" : "text-zinc-700"}`}>
                      {opt.label}
                    </p>
                    <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
                      {opt.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
          <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 ml-1 block border-b border-zinc-100 pb-2">
            Môi trường soạn thảo
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                id: "json",
                label: "Soạn thảo chuẩn",
                desc: "Soạn thảo dạng Block hiện đại, trực quan, dễ dùng.",
                icon: FileText,
              },
              {
                id: "latex",
                label: "Soạn thảo LaTeX",
                desc: "Soạn thảo mã nguồn LaTeX chuyên nghiệp dành cho tài liệu học thuật.",
                icon: Code,
              },
            ].map((opt) => {
              const Icon = opt.icon;
              const isSelected = contentFormat === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setContentFormat(opt.id)}
                  className={`p-5 border text-left flex items-start gap-4 rounded-3xl transition-all duration-200 group ${isSelected ? "border-black bg-zinc-50 shadow-sm" : "bg-white border-zinc-200 hover:border-zinc-300 hover:shadow-sm"}`}
                >
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 transition-colors ${isSelected ? "bg-black text-white" : "bg-zinc-50 text-zinc-400 border border-zinc-100 group-hover:text-zinc-600"}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="space-y-1.5 pt-0.5">
                    <p className={`text-sm font-bold ${isSelected ? "text-zinc-900" : "text-zinc-700"}`}>
                      {opt.label}
                    </p>
                    <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-relaxed">
                      {opt.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-zinc-100 shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 bg-zinc-50 px-4 py-2 rounded-2xl border border-zinc-100">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
          <div className="flex flex-col">
            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">Trạng thái hệ thống</span>
            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-900">Sẵn sàng thiết lập không gian</span>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading || !title.trim()}
          className="h-12 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-3 rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md w-full sm:w-auto group"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>Bắt đầu soạn thảo <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" /></>
          )}
        </button>
      </div>
    </form>
  );
}
