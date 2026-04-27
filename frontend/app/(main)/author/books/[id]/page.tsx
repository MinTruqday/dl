"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import { 
  ChevronLeft, 
  Settings, 
  Users, 
  Lock, 
  Clock, 
  Eye, 
  FileText, 
  DollarSign, 
  Save, 
  Trash2,
  Image as ImageIcon
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { getToken } from "@/app/lib/api";

export default function BookManagementPage() {
  const { id } = useParams();
  const router = useRouter();
  const [book, setBook] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("general");
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    const fetchBook = async () => {
      const token = getToken();
      try {
        const res = await fetch(`${API_URL}/books/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) setBook(await res.json());
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchBook();
  }, [id, API_URL]);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleUpdatePricing = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    const formData = new FormData(e.target as HTMLFormElement);
    try {
      const res = await fetch(`${API_URL}/author/books/${id}/pricing`, {
        method: "PUT",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          price_coins: parseInt(formData.get("price") as string),
          is_drm_protected: formData.get("drm") === "on"
        })
      });
      if (res.ok) showToast("Đã cập nhật giá bán.");
    } catch (e) { showToast("Cập nhật thất bại."); }
  };

  const handleSetPassword = async (password: string) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/books/${id}/password`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });
      if (res.ok) showToast("Đã cài đặt mật khẩu.");
    } catch (e) { showToast("Lỗi khi cài mật khẩu."); }
  };

  const handleSetFreePreview = async (chapterIds: string[]) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/books/${id}/free-preview`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ chapter_ids: chapterIds })
      });
      if (res.ok) showToast("Đã cập nhật chương đọc thử.");
    } catch (e) { showToast("Cập nhật thất bại."); }
  };

  const handleSchedulePublish = async (publishAt: string) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/books/${id}/schedule`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ publish_at: publishAt })
      });
      if (res.ok) showToast("Đã lên lịch xuất bản.");
      else {
        const data = await res.json();
        showToast(data.detail || "Lỗi khi lên lịch.");
      }
    } catch (e) { showToast("Lỗi khi lên lịch."); }
  };

  const handleInviteCoauthor = async (userIdOrEmail: string) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/books/${id}/coauthors`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ user_id_or_email: userIdOrEmail })
      });
      if (res.ok) showToast("Đã gửi lời mời đồng tác giả.");
      else {
        const data = await res.json();
        showToast(data.detail || "Lỗi khi mời.");
      }
    } catch (e) { showToast("Lỗi khi mời."); }
  };

  if (loading) return <AppShell><div className="flex items-center justify-center min-h-screen"><div className="w-8 h-8 border-2 border-black border-t-transparent animate-spin" /></div></AppShell>;
  if (!book) return <AppShell><div className="text-center py-20">Không tìm thấy tài liệu.</div></AppShell>;

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto px-6 py-12 animate-in fade-in duration-500">
        <Link href="/author/dashboard" className="inline-flex items-center gap-1.5 text-[12px] font-bold tracking-widest text-zinc-400 hover:text-zinc-900 mb-8 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Quay lại bảng điều khiển
        </Link>

        <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-12">
          <div className="flex gap-6 items-start">
            <div className="w-24 h-32 bg-zinc-50 border border-zinc-200 flex items-center justify-center shrink-0">
              {book.cover_url ? <img src={book.cover_url} className="w-full h-full object-cover" /> : <FileText className="w-8 h-8 text-zinc-200" />}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-900 tracking-tighter mb-2">{book.title}</h1>
              <p className="text-zinc-500 text-xs mb-4">ID: {id}</p>
              <div className="flex gap-4">
                <Link href={`/editor/${id}`} className="px-4 py-2 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-colors">Tiếp tục viết</Link>
                <button className="px-4 py-2 border border-zinc-200 text-[12px] font-bold tracking-widest hover:border-zinc-900 transition-colors">Xem trước</button>
              </div>
            </div>
          </div>
        </div>


        <div className="flex border-b border-zinc-200 mb-12 overflow-x-auto no-scrollbar">
          <TabButton active={activeTab === "general"} onClick={() => setActiveTab("general")} label="Tổng quan" icon={<Settings className="w-4 h-4" />} />
          <TabButton active={activeTab === "monetize"} onClick={() => setActiveTab("monetize")} label="Doanh thu & Bảo vệ" icon={<DollarSign className="w-4 h-4" />} />
          <TabButton active={activeTab === "access"} onClick={() => setActiveTab("access")} label="Quyền truy cập" icon={<Lock className="w-4 h-4" />} />
          <TabButton active={activeTab === "publish"} onClick={() => setActiveTab("publish")} label="Xuất bản" icon={<Clock className="w-4 h-4" />} />
          <TabButton active={activeTab === "team"} onClick={() => setActiveTab("team")} label="Đồng tác giả" icon={<Users className="w-4 h-4" />} />
          <TabButton active={activeTab === "coupons"} onClick={() => setActiveTab("coupons")} label="Mã giảm giá" icon={<DollarSign className="w-4 h-4" />} />
        </div>


        <div className="min-h-[400px]">
          {activeTab === "general" && <GeneralSettings book={book} />}
          {activeTab === "monetize" && <MonetizeSettings book={book} onSave={handleUpdatePricing} />}
          {activeTab === "access" && <AccessSettings book={book} onSetPassword={handleSetPassword} onSetFreePreview={handleSetFreePreview} />}
          {activeTab === "publish" && <PublishSettings book={book} onSchedule={handleSchedulePublish} />}
          {activeTab === "team" && <TeamSettings book={book} onInvite={handleInviteCoauthor} />}
          {activeTab === "coupons" && <CouponSettings book={book} id={id as string} />}
        </div>
      </div>

      {toastMsg && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-zinc-900 text-white px-6 py-3 text-[12px] font-bold tracking-widest shadow-xl animate-in slide-in-from-bottom-2 duration-300">
          {toastMsg}
        </div>
      )}
    </AppShell>
  );
}

function TabButton({ active, onClick, label, icon }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-2 px-6 py-4 text-[12px] font-bold tracking-widest transition-all relative whitespace-nowrap ${
        active ? "text-zinc-900" : "text-zinc-400 hover:text-zinc-600"
      }`}
    >
      {icon}
      {label}
      {active && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-900" />}
    </button>
  );
}

function GeneralSettings({ book }: any) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-12 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="space-y-6">
        <div>
          <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-2">Tiêu đề tài liệu</label>
          <input type="text" defaultValue={book.title} className="w-full p-4 border border-zinc-200 focus:border-zinc-900 outline-none transition-colors text-sm" />
        </div>
        <div>
          <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-2">Đường dẫn (Slug)</label>
          <input type="text" defaultValue={book.slug} className="w-full p-4 border border-zinc-200 focus:border-zinc-900 outline-none transition-colors text-sm" />
        </div>
        <div>
          <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-2">Mô tả ngắn</label>
          <textarea rows={4} defaultValue={book.description} className="w-full p-4 border border-zinc-200 focus:border-zinc-900 outline-none transition-colors text-sm" />
        </div>
        <button className="px-8 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-colors flex items-center gap-2">
          <Save className="w-4 h-4" /> Lưu thông tin
        </button>
      </div>
      <div>
        <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-4">Ảnh bìa</label>
        <div className="aspect-[3/4] max-w-[240px] bg-zinc-50 border border-zinc-200 flex flex-col items-center justify-center gap-4 group relative overflow-hidden">
          {book.cover_url ? (
            <img src={book.cover_url} className="w-full h-full object-cover" />
          ) : (
            <ImageIcon className="w-12 h-12 text-zinc-200" />
          )}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
             <button className="bg-white text-black px-4 py-2 text-[12px] font-bold tracking-widest">Thay đổi ảnh</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MonetizeSettings({ book, onSave }: any) {
  return (
    <form onSubmit={onSave} className="max-w-xl space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-1">Cấu hình giá bán</h3>
        <p className="text-zinc-500 text-xs mb-6">Mặc định là 0 nếu tài liệu này miễn phí.</p>
        <div className="relative max-w-[200px]">
          <input name="price" type="number" defaultValue={book.price_coins || 0} className="w-full p-4 pr-12 border border-zinc-200 focus:border-zinc-900 outline-none text-lg font-bold" />
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[12px] font-bold text-zinc-400 tracking-widest">Coin</span>
        </div>
      </div>
      <div className="p-6 border border-zinc-200 bg-zinc-50">
        <label className="flex items-center gap-4 cursor-pointer">
          <input name="drm" type="checkbox" defaultChecked={book.is_drm_protected} className="w-5 h-5 accent-zinc-900" />
          <div>
            <p className="text-sm font-bold text-zinc-900 tracking-tight">Kích hoạt bảo vệ bản quyền</p>
            <p className="text-zinc-500 text-xs mt-1">Ngăn chặn sao chép và tải về trái phép khi chưa mua.</p>
          </div>
        </label>
      </div>
      <button type="submit" className="px-8 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-colors flex items-center gap-2">
        <Save className="w-4 h-4" /> Lưu cấu hình tài chính
      </button>
    </form>
  );
}

function AccessSettings({ book, onSetPassword, onSetFreePreview }: any) {
  const [password, setPassword] = useState("");
  const [selectedPreviewIds, setSelectedPreviewIds] = useState<string[]>(
    (book.chapters || []).filter((ch: any) => !ch.is_premium).map((ch: any) => ch.id)
  );

  return (
    <div className="max-w-xl space-y-12 animate-in fade-in slide-in-from-top-4 duration-500">
      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-1">Mật khẩu truy cập</h3>
        <p className="text-zinc-500 text-xs mb-6">Thiết lập mật khẩu nếu bạn muốn tài liệu chỉ dành cho người có link và pass.</p>
        <div className="flex gap-4">
          <input 
            type="password" 
            placeholder="Nhập mật khẩu mới" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="flex-1 p-4 border border-zinc-200 focus:border-zinc-900 outline-none text-sm" 
          />
          <button 
            onClick={() => onSetPassword(password)}
            className="px-6 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800"
          >Cài đặt</button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-1 tracking-tight">Chương đọc thử</h3>
        <p className="text-zinc-500 text-xs mb-6">Chọn các chương mà độc giả có thể đọc miễn phí trước khi quyết định mua.</p>
        <div className="border border-zinc-200 divide-y divide-zinc-100">
          {(book.chapters || []).map((ch: any) => (
            <div key={ch.id} className="p-4 flex items-center justify-between hover:bg-zinc-50">
               <span className="text-xs font-bold text-zinc-900">{ch.title}</span>
               <input 
                type="checkbox" 
                checked={selectedPreviewIds.includes(ch.id)}
                onChange={(e) => {
                  const ids = e.target.checked 
                    ? [...selectedPreviewIds, ch.id]
                    : selectedPreviewIds.filter(id => id !== ch.id);
                  setSelectedPreviewIds(ids);
                }}
                className="w-4 h-4 accent-zinc-900" 
              />
            </div>
          ))}
          {(book.chapters || []).length === 0 && <p className="p-6 text-center text-zinc-400 text-[12px] font-bold tracking-widest">Chưa có chương nào</p>}
        </div>
        <button 
          onClick={() => onSetFreePreview(selectedPreviewIds)}
          className="mt-6 px-8 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest"
        >Lưu chương đọc thử</button>
      </div>
    </div>
  );
}

function PublishSettings({ book, onSchedule }: any) {
  const [publishAt, setPublishAt] = useState("");

  return (
    <div className="max-w-xl space-y-12 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="p-8 border border-zinc-900">
        <h3 className="text-sm font-bold text-zinc-900 mb-1 tracking-tight">Trạng thái hiện tại: {book.status === 'published' ? 'Đã công khai' : 'Bản nháp'}</h3>
        <p className="text-zinc-500 text-xs mb-8">Khi xuất bản, tài liệu sẽ xuất hiện trên trang Khám phá và Feed của người theo dõi.</p>
        <button className={`w-full py-4 text-[12px] font-bold tracking-widest transition-colors ${
          book.status === 'published' ? 'border border-zinc-200 text-zinc-400 hover:text-zinc-900 hover:border-zinc-900' : 'bg-zinc-900 text-white hover:bg-zinc-800'
        }`}>
          {book.status === 'published' ? 'Gỡ bỏ (Hạ xuống bản nháp)' : 'Xuất bản ngay lập tức'}
        </button>
      </div>

      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-1 tracking-tight">Lên lịch xuất bản tự động</h3>
        <p className="text-zinc-500 text-xs mb-6">Chọn thời điểm tài liệu sẽ được tự động công khai.</p>
        <div className="flex gap-4">
          <input 
            type="datetime-local" 
            value={publishAt}
            onChange={(e) => setPublishAt(e.target.value)}
            className="flex-1 p-4 border border-zinc-200 focus:border-zinc-900 outline-none text-sm" 
          />
          <button 
            onClick={() => onSchedule(publishAt)}
            className="px-6 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800"
          >Đặt lịch</button>
        </div>
      </div>
    </div>
  );
}

function TeamSettings({ book, onInvite }: any) {
  const [inviteValue, setInviteValue] = useState("");

  return (
    <div className="max-w-xl space-y-12 animate-in fade-in slide-in-from-top-4 duration-500">
      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-1 tracking-tight">Mời đồng tác giả</h3>
        <p className="text-zinc-500 text-xs mb-6">Đồng tác giả có quyền sửa đổi nội dung và cấu hình tài liệu này.</p>
        <div className="flex gap-4">
          <input 
            type="text" 
            placeholder="Nhập ID người dùng hoặc Email" 
            value={inviteValue}
            onChange={(e) => setInviteValue(e.target.value)}
            className="flex-1 p-4 border border-zinc-200 focus:border-zinc-900 outline-none text-sm" 
          />
          <button 
            onClick={() => onInvite(inviteValue)}
            className="px-6 py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800"
          >Gửi lời mời</button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-6 tracking-tight">Danh sách đội ngũ</h3>
        <div className="border border-zinc-200 divide-y divide-zinc-100">
          <div className="p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-zinc-100 rounded-full" />
              <div>
                <p className="text-xs font-bold text-zinc-900">Bạn (Chủ sở hữu)</p>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest">Toàn quyền</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CouponSettings({ book, id }: any) {
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newCoupon, setNewCoupon] = useState({ code: "", discount_percent: 10, max_uses: 100, expires_at: "" });
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchCoupons();
  }, [id, API_URL]);

  const fetchCoupons = async () => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/coupons`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const all = await res.json();
        setCoupons(all.filter((c: any) => c.book_id === id));
      }
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const handleCreate = async () => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/author/coupons`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ ...newCoupon, book_id: id })
      });
      if (res.ok) {
        setNewCoupon({ code: "", discount_percent: 10, max_uses: 100, expires_at: "" });
        fetchCoupons();
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="max-w-xl space-y-12 animate-in fade-in slide-in-from-top-4 duration-500">
      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-6 tracking-tight">Tạo mã giảm giá</h3>
        <div className="space-y-4">
          <input 
            type="text" 
            placeholder="Mã (Ví dụ: DOCLIB20)" 
            value={newCoupon.code}
            onChange={(e) => setNewCoupon({...newCoupon, code: e.target.value})}
            className="w-full p-4 border border-zinc-200 outline-none text-sm font-bold tracking-widest" 
          />
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-1">% Giảm</label>
              <input 
                type="number" 
                value={newCoupon.discount_percent}
                onChange={(e) => setNewCoupon({...newCoupon, discount_percent: parseInt(e.target.value)})}
                className="w-full p-4 border border-zinc-200 outline-none text-sm" 
              />
            </div>
            <div className="flex-1">
              <label className="block text-[12px] font-bold tracking-widest text-zinc-400 mb-1">Số lượng</label>
              <input 
                type="number" 
                value={newCoupon.max_uses}
                onChange={(e) => setNewCoupon({...newCoupon, max_uses: parseInt(e.target.value)})}
                className="w-full p-4 border border-zinc-200 outline-none text-sm" 
              />
            </div>
          </div>
          <button 
            onClick={handleCreate}
            className="w-full py-4 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800"
          >Phát hành mã</button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-zinc-900 mb-6 tracking-tight">Mã đang hoạt động</h3>
        <div className="divide-y divide-zinc-100 border border-zinc-200">
          {coupons.length === 0 ? (
            <p className="p-8 text-center text-zinc-400 text-[12px] font-bold tracking-widest">Chưa có mã nào</p>
          ) : coupons.map(c => (
            <div key={c.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-bold text-zinc-900 tracking-widest">{c.code}</p>
                <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">
                  Giảm {c.discount_percent}% • {c.used_count}/{c.max_uses} Lượt dùng
                </p>
              </div>
              <div className={`px-2 py-1 text-[10px] font-bold tracking-widest ${c.is_active ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-400'}`}>
                {c.is_active ? 'Hoạt động' : 'Hết hạn'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
