"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/app/lib/api";
import { 
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
  PlusCircle
} from "lucide-react";
import Link from "next/link";
import { Notification } from "@/app/components/NotificationToast";
import { formatError } from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";

export default function CreateDocumentPage() {
  const router = useRouter();
  const { user } = useAuth() as any;
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [publisherName, setPublisherName] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/author/documents?status=draft`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDrafts(data.data || data);
      }
    } catch (err) {
      console.error("Lỗi tải bản nháp:", err);
    } finally {
      setLoadingDrafts(false);
    }
  };

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          title,
          slug: `${slugify(title)}-${Date.now()}`,
          description,
          publisher_name: publisherName,
          visibility,
          status: "draft",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setNotification({ type: "success", text: "Khởi tạo tác phẩm thành công!" });
        setTimeout(() => {
          router.push(`/studio?document=${data.data.id || data.data._id}`);
        }, 1000);
      } else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Không thể tạo tài liệu lúc này." });
      }
    } catch (err) {
      setNotification({ type: "error", text: "Lỗi kết nối máy chủ." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Header - Premium Standard */}
      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Khởi tạo tri thức
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              New Knowledge Creation <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
             <PenTool className="w-4 h-4" /> Studio Sáng tác Chuyên nghiệp
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Sidebar Controls */}
        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Settings className="w-4 h-4 text-zinc-300" /> Thiết lập cơ bản
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "step1", label: "Thông tin sơ bộ", icon: Info },
                { id: "step2", label: "Lưu trữ", icon: FolderOpen },
                { id: "step3", label: "Cấu hình AI", icon: ShieldCheck },
              ].map((step) => (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                    activeStep === step.id
                      ? "bg-black text-white border-black shadow-xl shadow-black/5"
                      : "bg-white text-zinc-400 border-zinc-50 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <step.icon className="w-4 h-4" /> {step.label}
                  </div>
                  {activeStep === step.id && <ArrowRight className="w-3.5 h-3.5" />}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/30 space-y-4">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Hỗ trợ sáng tác</div>
             <p className="text-[11px] font-medium text-zinc-400 leading-relaxed italic">
               "Hãy bắt đầu với một tiêu đề bao quát và một tóm tắt đủ sức hấp dẫn để AI có thể hiểu đúng linh hồn tác phẩm của bạn."
             </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <div 
          className="lg:col-span-9 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {activeStep === "step1" ? (
            <form onSubmit={handleCreate} className="space-y-12">
            <div className="bg-white border border-zinc-100 p-10 md:p-16 space-y-16 hover:border-black transition-all duration-700 shadow-2xl shadow-black/[0.02]">
               <div className="space-y-12">
                  {/* Title Field */}
                  <div className="space-y-6 group">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest group-focus-within:text-black transition-colors">Tiêu đề tác phẩm</label>
                    <input
                      required
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Nhập tiêu đề tri thức"
                      className="w-full h-16 text-3xl font-bold border-b border-zinc-100 focus:border-black bg-transparent transition-all outline-none placeholder:text-zinc-100 tracking-tight"
                    />
                  </div>

                  {/* Publisher Field */}
                  <div className="space-y-6 group">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest group-focus-within:text-black transition-colors">Người đăng / Publisher</label>
                    <input
                      readOnly={user?.role === "admin"}
                      type="text"
                      value={publisherName}
                      onChange={(e) => setPublisherName(e.target.value)}
                      placeholder="Tên tác giả hiển thị"
                      className={`w-full h-16 text-xl font-bold border-b border-zinc-100 focus:border-black bg-transparent transition-all outline-none placeholder:text-zinc-100 tracking-tight ${user?.role === 'admin' ? 'opacity-50 cursor-not-allowed' : ''}`}
                    />
                    {user?.role === "admin" && (
                      <p className="text-[9px] font-medium text-zinc-300 italic">Mặc định là DocLib đối với Quản trị viên.</p>
                    )}
                  </div>

                  {/* Description Field */}
                  <div className="space-y-6 group">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest group-focus-within:text-black transition-colors">Tóm tắt nội dung (Tùy chọn)</label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Đôi dòng mô tả về giá trị tác phẩm mang lại"
                      className="w-full min-h-[120px] text-lg font-medium border-b border-zinc-100 focus:border-black bg-transparent transition-all outline-none placeholder:text-zinc-100 leading-relaxed py-4 resize-none"
                    />
                  </div>

                  {/* Visibility Selection */}
                  <div className="space-y-8">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Chế độ hiển thị</label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        { id: "public", label: "CÔNG KHAI", desc: "Mọi độc giả đều có thể tiếp cận.", icon: Globe },
                        { id: "private", label: "RIÊNG TƯ", desc: "Chỉ bạn hoặc cộng tác viên.", icon: Lock }
                      ].map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setVisibility(opt.id)}
                          className={`p-8 border text-left transition-all duration-500 flex flex-col gap-6 ${
                            visibility === opt.id ? "bg-black text-white border-black shadow-2xl shadow-black/20" : "bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black"
                          }`}
                        >
                          <opt.icon className={`w-6 h-6 ${visibility === opt.id ? 'text-white' : 'text-zinc-100'}`} />
                          <div className="space-y-1">
                            <p className="text-sm font-bold tracking-tight">{opt.label}</p>
                            <p className="text-[10px] font-medium opacity-60 leading-relaxed">{opt.desc}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
               </div>
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 pt-8 border-t border-zinc-50">
               <div className="flex items-center gap-6">
                  {/* Small Preview Mockup */}
                  <div className="w-16 h-20 bg-zinc-50 border border-zinc-100 overflow-hidden relative grayscale opacity-40 shrink-0">
                     <div className="w-full h-full flex items-center justify-center">
                        <FileText className="w-6 h-6 text-zinc-100 stroke-[1]" />
                     </div>
                  </div>
                  <div className="space-y-1">
                     <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Trạng thái khởi tạo: {publisherName}</p>
                     <p className="text-[11px] font-medium text-black">Sẵn sàng thiết lập không gian soạn thảo</p>
                  </div>
               </div>

               <button
                 type="submit"
                 disabled={loading || !title.trim()}
                 className="w-full md:w-auto h-16 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.3em] hover:bg-zinc-800 transition-all active:scale-[0.98] disabled:opacity-30 flex items-center justify-center gap-4 shadow-2xl shadow-black/10"
               >
                 {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <BookOpen className="w-5 h-5" />}
                 Bắt đầu soạn thảo
               </button>
            </div>
          </form>
          ) : activeStep === "step2" ? (
            <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
               <div className="bg-white border border-zinc-100 p-10 md:p-16 space-y-12">
                  <div className="space-y-2">
                    <h3 className="text-3xl font-bold tracking-tighter uppercase">Lưu trữ bản nháp</h3>
                    <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Tiếp tục hành trình xây dựng tri thức của bạn</p>
                  </div>

                  {loadingDrafts ? (
                    <div className="py-24 flex justify-center">
                      <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
                    </div>
                  ) : drafts.length === 0 ? (
                    <div className="py-24 text-center border border-dashed border-zinc-100 bg-zinc-50/20">
                      <FolderOpen className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                      <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Không có bản nháp nào được lưu trữ</p>
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {drafts.map((draft: any) => (
                        <button
                          key={draft._id || draft.id}
                          onClick={() => router.push(`/studio?document=${draft._id || draft.id}`)}
                          className="group flex items-center justify-between p-8 border border-zinc-100 hover:border-black transition-all duration-700 text-left bg-white"
                        >
                          <div className="flex items-center gap-8">
                            <div className="w-16 h-16 bg-zinc-50 flex items-center justify-center group-hover:bg-black group-hover:text-white transition-all duration-500 shrink-0">
                               <FileText className="w-8 h-8 text-zinc-200" />
                            </div>
                            <div className="space-y-1">
                               <h4 className="font-bold text-2xl text-black group-hover:translate-x-1 transition-transform tracking-tighter">{draft.title}</h4>
                               <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                 Lần cuối chỉnh sửa: {new Date(draft.updated_at || draft.created_at).toLocaleDateString("vi-VN")}
                               </p>
                            </div>
                          </div>
                          <ArrowRight className="w-6 h-6 text-zinc-100 group-hover:text-black group-hover:translate-x-2 transition-all" />
                        </button>
                      ))}
                    </div>
                  )}
               </div>
            </div>
          ) : (
             <div className="bg-white border border-zinc-100 p-20 text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <ShieldCheck className="w-16 h-16 text-zinc-100 mx-auto stroke-[1]" />
                <div className="space-y-2">
                   <h3 className="text-2xl font-bold tracking-tighter uppercase">Cấu hình tri thức AI</h3>
                   <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Tính năng đang được phát triển</p>
                </div>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
