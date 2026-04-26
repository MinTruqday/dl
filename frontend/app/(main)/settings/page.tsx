"use client";

import { useEffect, useState } from "react";
import { Lock, Eye, Bell, Monitor, Type, Shield, Trash2, Smartphone, Globe, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/settings`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
        });
        if (res.ok) setSettings(await res.json());
        else setSettings({
            appearance: "light",
            fontSize: "medium",
            notifications: true,
            privacyProfile: "public",
            privacyActivity: true,
            twoFactor: false,
            notifyCommunity: { email: true, inapp: true },
            notifyFinance: { email: true, inapp: true },
            notifyUpdates: { email: false, inapp: true },
            notifyNewsletter: { email: true, inapp: false }
        });
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetchSettings();
  }, []);

  const toggleSetting = (key: string) => {
    setSettings((prev: any) => ({ ...prev, [key]: typeof prev[key] === "boolean" ? !prev[key] : prev[key] }));
  };

  const toggleNestedSetting = (category: string, key: string) => {
    setSettings((prev: any) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: !prev[category][key]
      }
    }));
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" /></div>;

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="border-b border-black pb-8 mb-12">
        <div className="flex items-center gap-3 mb-2">
           <Monitor className="w-5 h-5 text-black" />
           <span className="text-[10px] font-bold tracking-widest text-zinc-400">Cấu hình cá nhân</span>
        </div>
        <h1 className="text-4xl font-black text-black tracking-tighter">Thiết lập hệ thống</h1>
      </header>

      <div className="space-y-12">
        <section className="space-y-6">
           <h2 className="text-xs font-black tracking-widest border-l-4 border-black pl-4">Hiển thị & Trải nghiệm</h2>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-zinc-100 p-6 space-y-4">
                 <div className="flex items-center gap-3">
                    <Type className="w-4 h-4" />
                    <span className="text-xs font-bold ">Kích thước chữ mặc định</span>
                 </div>
                 <div className="flex gap-2">
                    {["small", "medium", "large"].map(s => (
                       <button 
                          key={s}
                          onClick={() => setSettings({...settings, fontSize: s})}
                          className={`flex-1 py-2 border text-[10px] font-bold  transition-all ${settings.fontSize === s ? 'bg-black text-white border-black' : 'hover:bg-zinc-50'}`}
                       >
                          {s === 'small' ? 'Nhỏ' : s === 'medium' ? 'Vừa' : 'Lớn'}
                       </button>
                    ))}
                 </div>
              </div>
              <div className="border border-zinc-100 p-6 space-y-4">
                 <div className="flex items-center gap-3">
                    <Globe className="w-4 h-4" />
                    <span className="text-xs font-bold ">Ngôn ngữ hệ thống</span>
                 </div>
                 <button className="w-full py-2 border bg-zinc-50 text-[10px] font-bold  tracking-widest cursor-not-allowed opacity-50">
                    Tiếng Việt (Mặc định)
                 </button>
              </div>
           </div>
        </section>

        <section className="space-y-6">
           <h2 className="text-xs font-black  tracking-widest border-l-4 border-black pl-4">Thiết bị & Phiên hoạt động</h2>
           <div className="border border-zinc-100 divide-y divide-zinc-50">
              <div className="p-6 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                 <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-zinc-100 flex items-center justify-center">
                       <Smartphone className="w-5 h-5 text-black" />
                    </div>
                    <div>
                       <p className="text-sm font-bold  tracking-tight">iPhone 15 Pro</p>
                       <p className="text-[10px] text-zinc-950 font-bold  tracking-widest flex items-center gap-1.5">
                           <span className="w-1.5 h-1.5 bg-black" /> Đang hoạt động • Hồ Chí Minh, VN
                       </p>
                    </div>
                 </div>
                 <span className="text-[9px] font-black  tracking-widest px-2 py-1 bg-zinc-100">Thiết bị này</span>
              </div>
              <div className="p-6 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                 <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-zinc-100 flex items-center justify-center">
                       <Monitor className="w-5 h-5 text-zinc-400" />
                    </div>
                    <div>
                       <p className="text-sm font-bold  tracking-tight">MacBook Pro M3</p>
                       <p className="text-[10px] text-zinc-400 font-bold  tracking-widest">Hoạt động 2 giờ trước • Hà Nội, VN</p>
                    </div>
                 </div>
                 <button className="text-[10px] font-bold  tracking-widest text-zinc-400 hover:text-black hover:underline transition-colors">Đăng xuất</button>
              </div>
           </div>
        </section>

        <section className="space-y-6">
           <h2 className="text-xs font-black  tracking-widest border-l-4 border-black pl-4">Quyền riêng tư & Bảo mật</h2>
           <div className="border border-black divide-y divide-zinc-100">
              <div className="p-6 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                 <div className="space-y-1">
                    <p className="text-sm font-bold  tracking-tight">Chế độ hồ sơ</p>
                    <p className="text-[10px] text-zinc-400 font-bold  tracking-widest">Cho phép người khác tìm thấy bạn</p>
                 </div>
                 <select 
                    value={settings.privacyProfile}
                    onChange={e => setSettings({...settings, privacyProfile: e.target.value})}
                    className="bg-transparent border border-zinc-200 p-2 text-xs font-bold outline-none"
                 >
                    <option value="public">Công khai</option>
                    <option value="private">Riêng tư</option>
                 </select>
              </div>
              <div className="p-6 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                 <div className="space-y-1">
                    <p className="text-sm font-bold  tracking-tight">Hiển thị hoạt động đọc</p>
                    <p className="text-[10px] text-zinc-400 font-bold  tracking-widest">Chia sẻ các đầu sách bạn đang đọc trên Feed</p>
                 </div>
                 <button 
                    onClick={() => toggleSetting("privacyActivity")}
                    className={`w-12 h-6 border transition-colors relative ${settings.privacyActivity ? 'bg-black border-black' : 'bg-zinc-100 border-zinc-200'}`}
                 >
                    <div className={`absolute top-1 w-4 h-4 bg-white transition-all ${settings.privacyActivity ? 'left-7' : 'left-1'}`} />
                 </button>
              </div>
              <div className="p-6 flex items-center justify-between hover:bg-zinc-50 transition-colors">
                 <div className="space-y-1">
                    <p className="text-sm font-bold  tracking-tight">Xác thực 2 lớp (2FA)</p>
                    <p className="text-[10px] text-zinc-400 font-bold  tracking-widest">Tăng cường bảo mật bằng mã OTP</p>
                 </div>
                 <Button variant="outline" className="text-[10px] font-bold  tracking-widest h-10 px-6 border-black text-black hover:bg-black hover:text-white transition-all">
                    Kích hoạt
                 </Button>
              </div>
           </div>
        </section>

        <section className="space-y-6">
           <h2 className="text-xs font-black  tracking-widest border-l-4 border-black pl-4">Xác minh danh tính</h2>
           <div className="border border-black p-8 space-y-6 bg-white">
              <div className="flex items-center gap-4">
                 <div className="w-12 h-12 bg-zinc-100 flex items-center justify-center border border-zinc-200">
                    <CheckCircle className="w-6 h-6 text-zinc-300" />
                 </div>
                 <div>
                    <h3 className="text-sm font-black  tracking-tight">Trở thành Tác giả xác minh</h3>
                    <p className="text-[10px] text-zinc-400 font-bold  tracking-widest leading-relaxed">
                       Nhận tích xanh để khẳng định uy tín và mở khóa các tính năng thương mại nâng cao.
                    </p>
                 </div>
              </div>
              
              <div className="space-y-4 pt-4 border-t border-zinc-100">
                 <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-zinc-500 ">Tiêu chuẩn tối thiểu:</span>
                    <span className="text-zinc-400  tracking-tighter">03/05 hoàn tất</span>
                 </div>
                 <div className="w-full h-1.5 bg-zinc-100">
                    <div className="w-3/5 h-full bg-black" />
                 </div>
              </div>

              <button className="w-full py-4 bg-zinc-100 text-zinc-400 text-[10px] font-bold  tracking-widest cursor-not-allowed">
                 Xác minh ngay
              </button>
           </div>
        </section>

        <section className="space-y-6">
           <h2 className="text-xs font-black  tracking-widest border-l-4 border-black pl-4">Cài đặt thông báo</h2>
           <div className="border border-zinc-100 divide-y divide-zinc-50 bg-white">
               {[
                  { id: "notifyCommunity", label: "Tương tác cộng đồng", desc: "Thông báo khi có người bình chọn, bình luận hoặc nhắc đến bạn." },
                  { id: "notifyFinance", label: "Giao dịch & Tài chính", desc: "Thông báo về việc mua tài liệu, tặng coin hoặc yêu cầu rút tiền." },
                  { id: "notifyUpdates", label: "Cập nhật tài liệu", desc: "Thông báo khi các tài liệu bạn theo dõi có chương mới." },
                  { id: "notifyNewsletter", label: "Bản tin DocLib", desc: "Cập nhật về các tính năng mới và cuộc thi sắp tới." }
               ].map((item, i) => (
                  <div key={i} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-zinc-50 transition-colors">
                     <div className="space-y-1">
                        <p className="text-sm font-black  tracking-tight">{item.label}</p>
                        <p className="text-[10px] text-zinc-400 font-medium leading-relaxed max-w-md">{item.desc}</p>
                     </div>
                     <div className="flex gap-6">
                        <div className="flex items-center gap-2">
                           <div 
                              onClick={() => toggleNestedSetting(item.id, 'email')}
                              className={`w-10 h-5 rounded-none p-1 transition-all cursor-pointer ${settings[item.id]?.email ? 'bg-black' : 'bg-zinc-200'}`}
                           >
                              <div className={`w-3 h-3 bg-white rounded-none transition-all ${settings[item.id]?.email ? 'translate-x-5' : ''}`} />
                           </div>
                           <span className="text-[9px] font-bold  tracking-widest">Email</span>
                        </div>
                        <div className="flex items-center gap-2">
                           <div 
                              onClick={() => toggleNestedSetting(item.id, 'inapp')}
                              className={`w-10 h-5 rounded-none p-1 transition-all cursor-pointer ${settings[item.id]?.inapp ? 'bg-black' : 'bg-zinc-200'}`}
                           >
                              <div className={`w-3 h-3 bg-white rounded-none transition-all ${settings[item.id]?.inapp ? 'translate-x-5' : ''}`} />
                           </div>
                           <span className="text-[9px] font-bold  tracking-widest">Hệ thống</span>
                        </div>
                     </div>
                  </div>
               ))}
           </div>
        </section>

        <section className="space-y-6">
           <h2 className="text-xs font-black  tracking-widest border-l-4 border-black pl-4">Dữ liệu tài khoản</h2>
           
           <div className="border border-zinc-100 p-8 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="space-y-2 text-center md:text-left">
                 <h3 className="text-sm font-black  tracking-tight">Trích xuất dữ liệu</h3>
                 <p className="text-[10px] text-zinc-400 font-bold  tracking-widest max-w-md leading-relaxed">
                    Tải về toàn bộ dữ liệu cá nhân, lịch sử đọc và bài viết của bạn dưới định dạng JSON.
                 </p>
              </div>
              <Button 
                variant="outline" 
                onClick={async () => {
                  try {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/takeout`, {
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
                    });
                    if (res.ok) {
                      const blob = await res.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `doclib_data_${new Date().getTime()}.json`;
                      a.click();
                    }
                  } catch (e) { console.error(e); }
                }}
                className="h-12 px-8 font-black text-[10px]  tracking-widest border-black"
              >
                 Trích xuất dữ liệu
              </Button>
           </div>

           <div className="border border-zinc-200 p-8 bg-zinc-50/50 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="space-y-2 text-center md:text-left">
                 <h3 className="text-sm font-black  tracking-tight text-black">Xóa vĩnh viễn tài khoản</h3>
                 <p className="text-[10px] text-zinc-500 font-bold  tracking-widest max-w-md leading-relaxed">
                    Hành động này sẽ xóa toàn bộ dữ liệu, tài liệu đã mua và không thể khôi phục theo quy định bảo mật.
                 </p>
              </div>
              <Button 
                variant="destructive" 
                onClick={async () => {
                  if (confirm("BẠN CÓ CHẮC CHẮN MUỐN XÓA TÀI KHOẢN? Hành động này không thể hoàn tác.")) {
                    try {
                      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile/gdpr/delete`, {
                        method: "POST",
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
                      });
                      if (res.ok) {
                        alert("Tài khoản của bạn đã được xóa. Chào tạm biệt.");
                        localStorage.clear();
                        window.location.href = "/";
                      }
                    } catch (e) { console.error(e); }
                  }
                }}
                className="h-12 px-8 font-black text-[10px]  tracking-widest"
              >
                 Xóa tài khoản
              </Button>
           </div>
        </section>

        <div className="pt-8 border-t border-zinc-100 flex justify-end">
           <Button className="h-12 px-12 font-black text-[10px]  tracking-widest bg-black text-white">
              Lưu toàn bộ thay đổi
           </Button>
        </div>
      </div>
    </div>
  );
}
