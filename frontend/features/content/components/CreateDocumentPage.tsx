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
            `/soan-thao?tai-lieu=${res.data?.id || res.data?._id || res.id || res._id}`,
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
    <form onSubmit={handleCreate} className="flex flex-col h-full font-sans text-[#1D1D1F]">


      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
              Tiêu đề tác phẩm <span className="text-[#FF3B30]">*</span>
            </label>
            <div className="relative">
              <BookOpen className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#C7C7CC]" />
              <input
                required
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Nhập tiêu đề tác phẩm..."
                className="w-full h-[52px] pl-12 pr-4 bg-white border border-transparent focus:border-[#0071E3] text-[15px] text-[#1D1D1F] rounded-[14px] transition-all duration-200 outline-none shadow-sm"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
              Người đăng / Nhà xuất bản
            </label>
            <div className="relative">
              <PenTool className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#C7C7CC]" />
              <input
                readOnly={user?.role === "admin"}
                type="text"
                value={publisherName}
                onChange={(e) => setPublisherName(e.target.value)}
                className={`w-full h-[52px] pl-12 pr-4 bg-white border border-transparent focus:border-[#0071E3] text-[15px] text-[#1D1D1F] rounded-[14px] transition-all duration-200 outline-none shadow-sm ${user?.role === "admin" ? "opacity-60 cursor-not-allowed" : ""}`}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
              Tóm tắt nội dung (Tùy chọn)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả ngắn gọn về nội dung tác phẩm..."
              className="w-full min-h-[140px] p-4 bg-white border border-transparent focus:border-[#0071E3] text-[15px] text-[#1D1D1F] rounded-[14px] transition-all duration-200 outline-none resize-none shadow-sm"
            />
          </div>
        </div>

        <div className="space-y-4">
          <label className="text-[15px] font-semibold text-[#1D1D1F] ml-1 block border-b border-[#E8E8ED] pb-3">
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
                  className={`p-6 text-left flex items-start gap-4 rounded-[18px] transition-all duration-200 group border ${isSelected ? "border-[#0071E3] bg-[#EBF4FF]" : "bg-white border-[#E8E8ED] hover:border-[#D2D2D7]"}`}
                >
                  <div className={`w-12 h-12 rounded-[14px] flex items-center justify-center shrink-0 transition-colors ${isSelected ? "bg-[#0071E3] text-white" : "bg-white border border-[#E8E8ED] text-[#6E6E73]"}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className={`text-[17px] font-semibold ${isSelected ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}>
                      {opt.label}
                    </p>
                    <p className="text-[13px] text-[#6E6E73] leading-relaxed">
                      {opt.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-4">
          <label className="text-[15px] font-semibold text-[#1D1D1F] ml-1 block border-b border-[#E8E8ED] pb-3">
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
                  className={`p-6 text-left flex items-start gap-4 rounded-[18px] transition-all duration-200 group border ${isSelected ? "border-[#0071E3] bg-[#EBF4FF]" : "bg-white border-[#E8E8ED] hover:border-[#D2D2D7]"}`}
                >
                  <div className={`w-12 h-12 rounded-[14px] flex items-center justify-center shrink-0 transition-colors ${isSelected ? "bg-[#0071E3] text-white" : "bg-white border border-[#E8E8ED] text-[#6E6E73]"}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className={`text-[17px] font-semibold ${isSelected ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}>
                      {opt.label}
                    </p>
                    <p className="text-[13px] text-[#6E6E73] leading-relaxed">
                      {opt.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-[#E8E8ED] shrink-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 px-4 py-3 bg-white rounded-[14px] shadow-sm">
          <div className="w-2.5 h-2.5 bg-[#34C759] rounded-full animate-pulse shadow-[0_0_8px_rgba(52,199,89,0.4)]" />
          <div className="flex flex-col">
            <span className="text-[12px] text-[#6E6E73] font-medium">Trạng thái hệ thống</span>
            <span className="text-[13px] font-semibold text-[#1D1D1F]">Sẵn sàng thiết lập không gian</span>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading || !title.trim()}
          className="h-[52px] px-8 bg-[#0071E3] text-white text-[15px] font-medium flex items-center justify-center gap-2 rounded-full disabled:opacity-50 transition-colors hover:bg-[#0077ED] w-full sm:w-auto"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>Bắt đầu soạn thảo <ArrowRight className="w-5 h-5" /></>
          )}
        </button>
      </div>
    </form>
  );
}
