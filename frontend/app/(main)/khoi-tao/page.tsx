"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDocumentAPI } from "@/services/document.service";
import { Loader2 } from "lucide-react";
import { useToast } from "@/contexts/Toast";
import { useAuth } from "@/contexts/Auth";

export default function CreateDocumentPage() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setPublisherName(user.role === "admin" ? "DocLib" : (user.full_name || ""));
    }
  }, [user]);

  const slugify = (text: string) => {
    return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[đĐ]/g, "d").replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
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
        status: "draft",
      });
      if (res) {
        showToast("Khởi tạo tác phẩm thành công.", "success");
        setTimeout(() => {
          router.push(`/sang-tac?tai-lieu=${res.data?.id || res.data?._id || res.id || res._id}`);
        }, 1000);
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi khởi tạo tài liệu.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleCreate} className="space-y-8">
      <div className="space-y-6">

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-black">Tiêu đề tác phẩm</label>
            <input
              required
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-sm font-semibold outline-none rounded-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-black">Người đăng / Nhà xuất bản</label>
            <input
              readOnly={user?.role === "admin"}
              type="text"
              value={publisherName}
              onChange={(e) => setPublisherName(e.target.value)}
              className={`w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none rounded-none ${user?.role === "admin" ? "opacity-50 cursor-not-allowed" : ""}`}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-black">Tóm tắt nội dung (Tùy chọn)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full min-h-[120px] p-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none resize-none rounded-none"
            />
          </div>

          <div className="space-y-3">
            <label className="text-sm font-semibold text-black">Chế độ hiển thị</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { id: "public", label: "Công khai", desc: "Mọi độc giả đều có thể tiếp cận." },
                { id: "private", label: "Riêng tư", desc: "Chỉ bạn hoặc cộng tác viên." },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setVisibility(opt.id)}
                  className={`p-4 border text-left flex items-start gap-4 rounded-none ${visibility === opt.id ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                >
                  <div className="space-y-1">
                    <p className={`text-sm font-semibold ${visibility === opt.id ? "text-white" : "text-black"}`}>{opt.label}</p>
                    <p className={`text-[10px] font-medium leading-relaxed ${visibility === opt.id ? "text-zinc-400" : "text-zinc-500"}`}>{opt.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-6 mt-8 border-t border-zinc-200 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="space-y-1">
              <p className="text-xs font-medium text-zinc-500">Khởi tạo bởi: {publisherName}</p>
              <p className="text-xs font-semibold text-black">Sẵn sàng thiết lập không gian soạn thảo</p>
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !title.trim()}
            className="w-full md:w-auto h-10 px-6 bg-black text-white text-sm font-semibold flex items-center justify-center gap-2 rounded-none border border-black disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Bắt đầu soạn thảo
          </button>
        </div>
      </div>
    </form>
  );
}
