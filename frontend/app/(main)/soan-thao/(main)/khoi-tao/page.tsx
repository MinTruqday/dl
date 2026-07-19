"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDocumentAPI } from "@/features/content/services/document.service";
import {
  Loader2,
  BookOpen,
  PenTool,
  Globe,
  Lock,
  Code,
  FileText,
  ArrowRight,
} from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import { useAuth } from "@/features/authentication/contexts/AuthContext";

export default function Page() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [contentFormat, setContentFormat] = useState("json");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setAuthorName(user.full_name || user.name || "Ẩn danh");
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
        author_name: authorName,
      });
      if (res) {
        showToast("Khởi tạo dữ liệu tác phẩm hoàn tất", "success");
        setTimeout(() => {
          router.push(
            `/soan-thao?tai-lieu=${res.data?.id || res.data?._id || res.id || res._id}`,
          );
        }, 1000);
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi khởi tạo dữ liệu tác phẩm", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleCreate}
      className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-6 font-sans text-[#1D1D1F]"
    >
      <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-6">Khởi tạo</h2>
      <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
              Tiêu đề tác phẩm <span className="text-[#FF3B30]">*</span>
            </label>
            <input
              required
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder=""
              className="apple-input w-full h-[48px]"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
                Người đăng
              </label>
              <input
                type="text"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
                className="apple-input w-full h-[48px]"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
                Nhà xuất bản
              </label>
              {user?.role === "admin" ? (
                <div className="apple-input w-full h-[48px] bg-[#E8E8ED] border-transparent px-4 flex items-center text-[#6E6E73] text-[15px] cursor-not-allowed">
                  {publisherName}
                </div>
              ) : (
                <input
                  type="text"
                  value={publisherName}
                  onChange={(e) => setPublisherName(e.target.value)}
                  className="apple-input w-full h-[48px]"
                />
              )}
            </div>
          </div>

            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
                Tóm tắt nội dung (Tùy chọn)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder=""
                className="apple-input w-full min-h-[100px] resize-none py-3"
              />
            </div>
        </div>

        <div className="space-y-4">
          <label className="text-[15px] font-semibold text-[#1D1D1F] ml-1 block pb-1">
            Môi trường soạn thảo
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { id: "json", label: "Soạn thảo chuẩn" },
              { id: "latex", label: "Soạn thảo LaTeX" },
            ].map((opt) => {
              const isSelected = contentFormat === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setContentFormat(opt.id)}
                  className={`h-[48px] rounded-full text-[15px] font-medium transition-colors ${isSelected ? "bg-[#0071E3] text-white" : "bg-white text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

      <div className="flex justify-end pt-4">
        <button
          type="submit"
          disabled={loading || !title.trim()}
          className="pill-button"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            "Bắt đầu soạn thảo"
          )}
        </button>
      </div>
    </form>
  );
}
