"use client";
import { useState } from "react";
import { Book, Shield, Zap, Code, Terminal, Database, Lock, Globe, Search } from "lucide-react";

export default function HelpPage() {
  const [search, setSearch] = useState("");
  const sections = [
    {
      title: "Dành cho Độc giả",
      icon: <Book className="w-6 h-6" />,
      items: [
        "Cách mua tài liệu bằng Coin",
        "Sử dụng công nghệ đọc văn bản AI",
        "Quản lý thư viện và lịch sử",
        "Hệ thống đánh giá"
      ]
    },
    {
      title: "Dành cho Tác giả",
      icon: <Zap className="w-6 h-6" />,
      items: [
        "Quy trình xuất bản tài liệu",
        "Thiết lập giá bán và Series",
        "Phân tích doanh thu & Độc giả",
        "Sử dụng công cụ AI viết lách"
      ]
    },
    {
      title: "Bảo mật & Quy tắc",
      icon: <Shield className="w-6 h-6" />,
      items: [
        "Quy tắc cộng đồng DocLib",
        "Chính sách bảo vệ bản quyền",
        "Xác thực 2 lớp (2FA)",
        "Quyền quản lý dữ liệu cá nhân"
      ]
    },
    {
      title: "Dành cho Nhà phát triển",
      icon: <Code className="w-6 h-6" />,
      items: [
        "Tài liệu giao diện lập trình",
        "Tích hợp thông báo tự động",
        "Hệ thống xác thực",
        "Triển khai hệ thống"
      ]
    }
  ];

  const filteredSections = sections.map(section => ({
    ...section,
    items: section.items.filter(item => 
      item.toLowerCase().includes(search.toLowerCase())
    )
  })).filter(section => section.items.length > 0);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="border-b-2 border-black pb-12 mb-16">
        <h1 className="text-6xl font-bold text-black tracking-tighter mb-8">Trung tâm Trợ giúp</h1>
        <div className="max-w-2xl relative">
           <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-black" />
           <input 
              type="text" 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Bạn cần hỗ trợ điều gì? (ví dụ: rút tiền, bản quyền)"
              className="w-full bg-white border-2 border-black p-6 pl-16 text-lg font-bold outline-none focus:bg-zinc-50 transition-all placeholder:text-zinc-300"
           />
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-24">
        {filteredSections.map((section, idx) => (
          <div key={idx} className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-black text-white flex items-center justify-center">
                {section.icon}
              </div>
              <h2 className="text-xl font-bold tracking-tighter">{section.title}</h2>
            </div>
            <ul className="space-y-4">
              {section.items.map((item, i) => (
                <li key={i} className="flex items-center justify-between group cursor-pointer hover:bg-zinc-50 p-2 -mx-2 transition-colors border-b border-zinc-100 last:border-0 pb-2">
                  <span className="text-sm font-bold text-zinc-600 group-hover:text-black">{item}</span>
                  <Terminal className="w-4 h-4 text-zinc-200 group-hover:text-black" />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mt-24 p-12 bg-black text-white text-center space-y-6">
        <h2 className="text-3xl font-bold tracking-tighter">Bạn là Nhà phát triển?</h2>
        <p className="text-zinc-400 text-sm max-w-xl mx-auto">
          Truy cập tài liệu API tự động để tích hợp các tính năng của DocLib vào ứng dụng của bạn.
        </p>
        <div className="flex justify-center gap-4 pt-4">
          <a href={`${process.env.NEXT_PUBLIC_API_URL}/docs`} target="_blank" className="bg-white text-black text-[12px] font-bold tracking-widest px-8 py-4 hover:bg-zinc-200 transition-colors">
            Tài liệu kỹ thuật
          </a>
          <a href={`${process.env.NEXT_PUBLIC_API_URL}/redoc`} target="_blank" className="border border-white text-white text-[12px] font-bold tracking-widest px-8 py-4 hover:bg-white hover:text-black transition-colors">
            Giao diện tham khảo
          </a>
        </div>
      </div>

      <div className="mt-24 space-y-8">
         <h2 className="text-xs font-bold tracking-widest border-l-4 border-black pl-4">Nhật ký cập nhật</h2>
         <div className="border border-zinc-100 divide-y divide-zinc-50">
            {[
              { date: "2024-04-24", event: "Triển khai hệ thống Báo cáo nội dung & Governance" },
              { date: "2024-04-24", event: "Cập nhật thuật toán Bảng vinh danh Độc giả & Tác giả" },
              { date: "2024-04-23", event: "Tích hợp trung tâm thông báo thời gian thực" },
              { date: "2024-04-22", event: "Mở rộng bảng thống kê doanh thu cho Tác giả" }
            ].map((log, i) => (
              <div key={i} className="py-4 flex items-center justify-between px-2">
                 <span className="text-[12px] font-bold text-zinc-400 tracking-widest">{log.date}</span>
                 <span className="text-xs font-bold tracking-tight">{log.event}</span>
              </div>
            ))}
         </div>
      </div>

      <footer className="mt-24 pt-12 border-t border-zinc-100 grid grid-cols-1 md:grid-cols-4 gap-12">
         <div className="space-y-2">
            <h4 className="text-[12px] font-bold tracking-widest text-zinc-400">Trạng thái hệ thống</h4>
            <div className="flex items-center gap-2">
               <div className="w-2 h-2 rounded-none bg-black animate-pulse" />
               <span className="text-[12px] font-bold tracking-tighter">Hệ thống: Trực tuyến</span>
            </div>
         </div>
         <div className="space-y-2">
            <h4 className="text-[12px] font-bold tracking-widest text-zinc-400">Phản hồi</h4>
            <p className="text-[12px] font-bold">24ms (Tối ưu)</p>
         </div>
         <div className="space-y-2">
            <h4 className="text-[12px] font-bold tracking-widest text-zinc-400">Phiên bản</h4>
            <p className="text-xs font-bold">DocLib v1.0.0</p>
         </div>
         <div className="space-y-2">
            <h4 className="text-[12px] font-bold tracking-widest text-zinc-400">Hỗ trợ</h4>
            <p className="text-xs font-bold">support@doclib.io</p>
         </div>
      </footer>
    </div>
  );
}
