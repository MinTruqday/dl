"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  createDocumentAPI,
  getMyDocumentsAPI,
} from "@/services/document.service";
import { API_URL } from "@/services/auth.service";
import {
  ChevronRight,
  BookOpen,
  Loader2,
  Sparkles,
  Globe,
  Lock,
  ArrowRight,
  Info,
  PenTool,
  Settings,
  ShieldCheck,
  FileText,
  FolderOpen,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";
import { useAuth } from "@/contexts/AuthContext";

export default function CreateDocumentPage() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [visible, setVisible] = useState(false);
  const [activeStep, setActiveStep] = useState("step1");
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState(false);

  useEffect(() => {
    if (activeStep === "step2") {
      fetchDrafts();
    }
  }, [activeStep]);

  const fetchDrafts = async () => {
    setLoadingDrafts(true);
    try {
      const data = await getMyDocumentsAPI();
      const list = data.data || data || [];
      setDrafts(list.filter((d: any) => d.status === "draft"));
    } catch (err) {
      showToast("Không thể tải danh sách bản nháp", "error");
    } finally {
      setLoadingDrafts(false);
    }
  };

  useEffect(() => {
    if (user) {
      if (user.role === "admin") {
        setPublisherName("DocLib");
      } else {
        setPublisherName(user.full_name || "");
      }
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
        status: "draft",
      });

      if (res) {
        showToast("Khởi tạo tác phẩm thành công.", "success");
        setTimeout(() => {
          router.push(
            `/studio?document=${res.data?.id || res.data?._id || res.id || res._id}`,
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">
            Khởi tạo nội dung
          </h1>
          <p className="text-zinc-500 text-sm font-medium">
            Khởi tạo & Thiết lập không gian soạn thảo
          </p>
        </div>
        <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-white border border-zinc-200 text-xs font-medium text-black rounded-none">
          <PenTool className="w-4 h-4" /> Studio sáng tác chuyên nghiệp
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Sáng tác
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "step1", label: "Thông tin sơ bộ" },
                { id: "step2", label: "Kho lưu trữ nháp" },
                { id: "step3", label: "Trí tuệ nhân tạo" },
              ].map((step) => (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none ${
                    activeStep === step.id
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent"
                  }`}
                >
                  {step.label}
                  {activeStep === step.id && (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6 border border-zinc-200 bg-zinc-50">
            <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest leading-relaxed">
              "Hãy bắt đầu với một tiêu đề bao quát và một tóm tắt đủ sức hấp dẫn để AI có thể hiểu đúng linh hồn tác phẩm của bạn."
            </p>
          </div>
        </aside>

        <main className="lg:col-span-9 space-y-6">
          {activeStep === "step1" ? (
            <form onSubmit={handleCreate} className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">Thông tin sơ bộ</h3>
                  <p className="text-xs text-zinc-500 mt-1">Cấu hình siêu dữ liệu cho tài liệu</p>
                </div>

                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Tiêu đề tác phẩm
                    </label>
                    <input
                      required
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-sm font-semibold outline-none rounded-none"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Người đăng / Nhà xuất bản
                    </label>
                    <input
                      readOnly={user?.role === "admin"}
                      type="text"
                      value={publisherName}
                      onChange={(e) => setPublisherName(e.target.value)}
                      className={`w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none rounded-none ${user?.role === "admin" ? "opacity-50 cursor-not-allowed" : ""}`}
                    />
                    {user?.role === "admin" && (
                      <p className="text-[10px] font-medium text-zinc-500 mt-1">
                        Mặc định là DocLib đối với Quản trị viên.
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Tóm tắt nội dung (Tùy chọn)
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full min-h-[120px] p-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none resize-none rounded-none"
                    />
                  </div>

                  <div className="space-y-3">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Chế độ hiển thị
                    </label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          id: "public",
                          label: "Công khai",
                          desc: "Mọi độc giả đều có thể tiếp cận.",
                          icon: Globe,
                        },
                        {
                          id: "private",
                          label: "Riêng tư",
                          desc: "Chỉ bạn hoặc cộng tác viên.",
                          icon: Lock,
                        },
                      ].map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setVisibility(opt.id)}
                          className={`p-4 border text-left flex items-start gap-4 rounded-none ${
                            visibility === opt.id
                              ? "bg-black text-white border-black"
                              : "bg-white text-zinc-500 border-zinc-200"
                          }`}
                        >
                          <opt.icon className="w-5 h-5 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <p className={`text-xs font-semibold uppercase tracking-widest ${visibility === opt.id ? "text-white" : "text-black"}`}>
                              {opt.label}
                            </p>
                            <p className={`text-[10px] font-medium leading-relaxed ${visibility === opt.id ? "text-zinc-400" : "text-zinc-500"}`}>
                              {opt.desc}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pt-6 mt-8 border-t border-zinc-200 flex flex-col md:flex-row items-center justify-between gap-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-14 bg-zinc-50 border border-zinc-200 flex items-center justify-center shrink-0 rounded-none">
                      <FileText className="w-5 h-5 text-zinc-400" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Khởi tạo bởi: {publisherName}
                      </p>
                      <p className="text-xs font-semibold text-black">
                        Sẵn sàng thiết lập không gian soạn thảo
                      </p>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !title.trim()}
                    className="w-full md:w-auto h-10 px-6 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 rounded-none border border-black disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <BookOpen className="w-4 h-4" />
                    )}
                    Bắt đầu soạn thảo
                  </button>
                </div>
              </div>
            </form>
          ) : activeStep === "step2" ? (
            <div className="border border-zinc-200 bg-white p-8 space-y-6">
              <div className="border-b border-zinc-200 pb-4">
                <h3 className="text-sm font-semibold text-black uppercase tracking-widest">
                  Lưu trữ bản nháp
                </h3>
                <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest mt-1">
                  Tiếp tục hành trình xây dựng nội dung của bạn
                </p>
              </div>

              {loadingDrafts ? (
                <div className="py-24 flex justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
                </div>
              ) : drafts.length === 0 ? (
                <div className="py-24 flex flex-col items-center justify-center text-center border border-zinc-200 bg-zinc-50 rounded-none">
                  <FolderOpen className="w-10 h-10 text-zinc-400 mb-4" />
                  <p className="text-xs font-semibold text-black uppercase tracking-widest">
                    Không có bản nháp nào được lưu trữ
                  </p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {drafts.map((draft: any) => (
                    <button
                      key={draft._id || draft.id}
                      onClick={() =>
                        router.push(
                          `/studio?document=${draft._id || draft.id}`,
                        )
                      }
                      className="group flex items-center justify-between p-4 border border-zinc-200 bg-white text-left rounded-none"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center shrink-0 rounded-none">
                          <FileText className="w-4 h-4 text-zinc-400" />
                        </div>
                        <div className="space-y-1">
                          <h4 className="font-semibold text-sm text-black truncate max-w-sm">
                            {draft.title}
                          </h4>
                          <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest">
                            Lần cuối chỉnh sửa:{" "}
                            {new Date(
                              draft.updated_at || draft.created_at,
                            ).toLocaleDateString("vi-VN")}
                          </p>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-zinc-400" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="border border-zinc-200 bg-zinc-50 p-24 text-center flex flex-col items-center justify-center space-y-6 rounded-none">
              <ShieldCheck className="w-10 h-10 text-zinc-400" />
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-black uppercase tracking-widest">
                  Cấu hình AI
                </h3>
                <p className="text-xs font-medium text-zinc-500">
                  Tính năng đang được phát triển
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
