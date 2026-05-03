"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Bookmark,
  FolderPlus,
  Grid,
  MoreVertical,
  Share2,
  Plus,
  Loader2,
  Search,
  Lock,
  Globe,
  ChevronRight,
  Sparkles,
  Filter,
  Layers,
  BookOpen,
} from "lucide-react";
import {
  getReadingListsAPI,
  createReadingListAPI,
  getMySeriesAPI,
  createSeriesAPI,
} from "@/services/read.service";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function CollectionsPage() {
  const { user } = useAuth() as any;
  const { showToast } = useToast();
  
  const [collections, setCollections] = useState<any[]>([]);
  const [series, setSeries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "public" | "private" | "series">("all");
  const [searchQuery, setSearchQuery] = useState("");
  
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<"collection" | "series">("collection");
  const [createForm, setCreateForm] = useState({
    name: "",
    description: "",
    is_public: true,
  });
  const [isCreating, setIsCreating] = useState(false);

  const canManageSeries = ["author", "moderator", "admin"].includes(user?.role?.toLowerCase() || "");

  const fetchData = useCallback(async () => {
    try {
      const [collRes, seriesRes] = await Promise.all([
        getReadingListsAPI(),
        canManageSeries ? getMySeriesAPI() : Promise.resolve({ data: [] })
      ]);
      
      const collData = collRes.data || collRes;
      setCollections(Array.isArray(collData) ? collData : []);
      
      const seriesData = seriesRes.data || seriesRes;
      setSeries(Array.isArray(seriesData) ? seriesData : []);
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [canManageSeries]);

  const handleCreate = async () => {
    if (!createForm.name.trim()) return;
    setIsCreating(true);
    try {
      if (createType === "collection") {
        await createReadingListAPI({
          name: createForm.name.trim(),
          description: createForm.description.trim(),
          is_public: createForm.is_public,
        });
        showToast("Đã kiến tạo bộ sưu tập mới", "success");
      } else {
        await createSeriesAPI({
          title: createForm.name.trim(),
          description: createForm.description.trim(),
        });
        showToast("Đã khởi tạo chuỗi tri thức mới", "success");
      }
      await fetchData();
      setIsCreateModalOpen(false);
      setCreateForm({ name: "", description: "", is_public: true });
    } catch (err: any) {
      showToast("Thao tác thất bại", "error");
    } finally {
      setIsCreating(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredItems = activeTab === "series" 
    ? series.filter(s => (s.title || "").toLowerCase().includes(searchQuery.toLowerCase()))
    : collections.filter((col) => {
        const matchesSearch = (col.name || "").toLowerCase().includes(searchQuery.toLowerCase());
        if (activeTab === "all") return matchesSearch;
        if (activeTab === "public") return matchesSearch && col.is_public;
        if (activeTab === "private") return matchesSearch && !col.is_public;
        return matchesSearch;
      });

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Bộ sưu tập
            </h1>
            <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-3">
              Kiến tạo và quản trị mạng lưới tri thức <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
            </p>
          </div>

          <div className="flex items-center gap-4">
            {canManageSeries && (
              <button
                onClick={() => {
                  setCreateType("series");
                  setIsCreateModalOpen(true);
                }}
                className="h-16 px-8 border border-zinc-100 text-black text-[10px] font-bold tracking-[0.2em] uppercase active:scale-95 flex items-center gap-3 rounded-sm transition-all hover:bg-zinc-50"
              >
                <Layers className="w-4 h-4" />
                Chuỗi tri thức
              </button>
            )}
            <button
              onClick={() => {
                setCreateType("collection");
                setIsCreateModalOpen(true);
              }}
              className="h-16 px-10 bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase active:scale-95 flex items-center gap-4 rounded-sm transition-transform"
            >
              <FolderPlus className="w-5 h-5" />
              Tạo danh sách
            </button>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12 transition-all duration-300 delay-100" style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}>
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
              <Filter className="w-4 h-4" /> Phân loại
            </div>
            <nav className="flex flex-col gap-1.5">
              {[
                { id: "all", label: "Tất cả danh sách", icon: Grid },
                { id: "public", label: "Công khai", icon: Globe },
                { id: "private", label: "Riêng tư", icon: Lock },
                ...(canManageSeries ? [{ id: "series", label: "Chuỗi tri thức", icon: Layers }] : []),
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`text-left px-6 py-4 text-[10px] font-bold uppercase tracking-widest border rounded-sm flex items-center justify-between transition-all group ${
                    activeTab === tab.id
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:border-zinc-300"
                  }`}
                >
                  {tab.label}
                  <tab.icon className={`w-3.5 h-3.5 ${activeTab === tab.id ? 'text-white' : 'text-zinc-200 group-hover:text-black'}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[10px] font-bold text-black uppercase tracking-[0.3em] px-1">
              <Search className="w-4 h-4" /> Tìm kiếm
            </div>
            <div className="relative">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-200" />
              <input
                placeholder=""
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-14 h-14 bg-white border border-zinc-100 focus:border-black outline-none text-[11px] font-bold uppercase tracking-widest rounded-sm transition-all"
              />
            </div>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/20 rounded-sm">
            <p className="text-[10px] font-bold text-zinc-300 leading-relaxed uppercase tracking-tight">
              Tổ chức tri thức khoa học giúp tối ưu hóa việc tiếp cận và ứng dụng thông tin
            </p>
          </div>
        </aside>

        <div className="lg:col-span-9">
          {filteredItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {filteredItems.map((item) => (
                <div
                  key={item._id}
                  className="group border border-zinc-100 p-10 bg-white flex flex-col justify-between min-h-[380px] relative overflow-hidden rounded-sm hover:border-black transition-all"
                >
                  <div className="relative z-10">
                    <div className="flex justify-between items-start mb-10">
                      <div className="w-14 h-14 border border-zinc-100 bg-white flex items-center justify-center rounded-sm transition-all group-hover:bg-black group-hover:text-white">
                        {activeTab === "series" ? <Layers className="w-6 h-6" /> : <Grid className="w-6 h-6" />}
                      </div>
                      <div className="flex gap-2">
                        <button className="p-3 text-zinc-200 hover:text-black transition-colors rounded-sm border border-transparent hover:border-zinc-100">
                          <Share2 className="w-4 h-4" />
                        </button>
                        <button className="p-3 text-zinc-200 hover:text-black transition-colors rounded-sm border border-transparent hover:border-zinc-100">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-4">
                        <h3 className="text-2xl font-bold tracking-tighter text-black">
                          {item.name || item.title}
                        </h3>
                        {activeTab !== "series" && (
                          item.is_public ? (
                            <Globe className="w-3.5 h-3.5 text-zinc-200" />
                          ) : (
                            <Lock className="w-3.5 h-3.5 text-zinc-200" />
                          )
                        )}
                        {activeTab === "series" && <Sparkles className="w-3.5 h-3.5 text-zinc-100" />}
                      </div>
                      <p className="text-sm font-medium text-zinc-400 line-clamp-3 leading-relaxed">
                        {item.description || "Thực thể tri thức này hiện chưa có thông tin tóm lược chi tiết"}
                      </p>
                    </div>
                  </div>

                  <div className="pt-10 border-t border-zinc-50 mt-10 relative z-10">
                    <div className="flex items-center justify-between mb-8">
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-black rounded-sm" />
                        <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-black">
                          {activeTab === "series" ? (item.documents?.length || 0) : (item.documents?.length || 0)} Thực thể
                        </span>
                      </div>
                      <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-[0.2em]">
                        {new Date(item.created_at).toLocaleDateString("vi-VN")}
                      </span>
                    </div>

                    <Link
                      href={activeTab === "series" ? `/series/${item._id}` : `/collection/${item._id}`}
                      className="flex items-center justify-between w-full h-16 px-8 bg-zinc-50 hover:bg-black hover:text-white transition-all rounded-sm group/btn"
                    >
                      <span className="text-[10px] font-bold tracking-[0.3em] uppercase">
                        Truy cập tri thức
                      </span>
                      <ArrowRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-2" />
                    </Link>
                  </div>
                </div>
              ))}

              <button
                onClick={() => {
                  setCreateType(activeTab === "series" ? "series" : "collection");
                  setIsCreateModalOpen(true);
                }}
                className="group border border-dashed border-zinc-100 p-10 flex flex-col items-center justify-center space-y-8 min-h-[380px] active:scale-[0.98] rounded-sm transition-all hover:border-zinc-300 hover:bg-zinc-50/30"
              >
                <div className="w-16 h-16 border border-zinc-100 flex items-center justify-center bg-white rounded-sm group-hover:bg-black group-hover:text-white transition-all">
                  <Plus className="w-7 h-7 text-zinc-100 group-hover:text-white" />
                </div>
                <div className="text-center">
                  <p className="text-[11px] font-bold text-black tracking-[0.3em] uppercase mb-3">
                    Thêm thực thể mới
                  </p>
                  <p className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">
                    Xây dựng và kiến tạo kho tàng của bạn
                  </p>
                </div>
              </button>
            </div>
          ) : (
            <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-white rounded-sm">
              <div className="w-20 h-20 border border-zinc-100 bg-white flex items-center justify-center mb-10 rounded-sm">
                <Bookmark className="w-8 h-8 text-zinc-100 stroke-[1]" />
              </div>
              <h2 className="text-3xl font-bold tracking-tighter text-black mb-4 uppercase">
                Chưa có dữ liệu
              </h2>
              <p className="text-[10px] font-bold text-zinc-300 mb-10 max-w-xs text-center uppercase tracking-[0.2em] leading-loose">
                Bắt đầu hành trình bằng cách khởi tạo danh sách đầu tiên
              </p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="h-16 px-14 bg-black text-white text-[10px] font-bold tracking-[0.3em] uppercase rounded-sm active:scale-95 transition-transform shadow-sm shadow-zinc-200"
              >
                Khởi tạo ngay
              </button>
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
        className="max-w-xl"
      >
        <ModalHeader>
          <div className="flex items-center gap-6">
            <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-sm text-black">
              {createType === "series" ? <Layers className="w-6 h-6" /> : <FolderPlus className="w-6 h-6" />}
            </div>
            <div>
              <ModalTitle>{createType === "series" ? "Khởi tạo chuỗi tri thức" : "Tạo bộ sưu tập mới"}</ModalTitle>
              <ModalDescription>Phân loại và kết nối các thực thể tri thức chuyên sâu</ModalDescription>
            </div>
          </div>
        </ModalHeader>
        <ModalContent className="space-y-10 pt-6">
          <div className="space-y-4">
            <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em] px-1">Tiêu đề thực thể</label>
            <input
              type="text"
              value={createForm.name}
              onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
              className="w-full h-16 border-b border-zinc-100 focus:border-black outline-none font-bold text-lg transition-all"
              placeholder=""
              autoFocus
            />
          </div>
          <div className="space-y-4">
            <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-[0.2em] px-1">Mô tả tóm lược</label>
            <textarea
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full min-h-[140px] p-6 bg-zinc-50/30 border border-zinc-100 text-sm font-medium focus:border-black outline-none rounded-sm resize-none transition-all leading-relaxed"
              placeholder=""
            />
          </div>
          {createType === "collection" && (
            <div className="flex items-center justify-between p-6 border border-zinc-100 rounded-sm">
              <div className="space-y-1">
                <h4 className="text-[10px] font-bold uppercase tracking-widest">Chế độ hiển thị</h4>
                <p className="text-[9px] text-zinc-400 font-bold uppercase tracking-tight">Công khai bộ sưu tập với cộng đồng</p>
              </div>
              <button
                onClick={() => setCreateForm({ ...createForm, is_public: !createForm.is_public })}
                className={`w-14 h-8 relative rounded-sm transition-colors border ${createForm.is_public ? "bg-black border-black" : "bg-zinc-200 border-zinc-200"}`}
              >
                <div className={`absolute top-1 w-6 h-6 bg-white rounded-sm transition-all ${createForm.is_public ? "left-7" : "left-1"}`} />
              </button>
            </div>
          )}
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() => setIsCreateModalOpen(false)}
            disabled={isCreating}
            className="flex-1 h-16 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest active:scale-[0.98] rounded-sm transition-all text-zinc-300 hover:text-black"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating || !createForm.name.trim()}
            className="flex-1 h-16 bg-black text-white text-[10px] font-bold uppercase tracking-[0.3em] active:scale-[0.98] rounded-sm transition-all disabled:opacity-30 flex items-center justify-center"
          >
            {isCreating ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận tạo"}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
