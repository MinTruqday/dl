"use client";

import React, { useState } from "react";
import { HelpCircle, Book, MessageCircle, Shield, LifeBuoy, Search } from "lucide-react";

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const faqs = [
    { q: "DocLib là gì?", a: "DocLib là nền tảng xuất bản và chia sẻ tài liệu trực tuyến, tập trung vào trải nghiệm đọc tối giản và hiệu quả." },
    { q: "Làm thế nào để trở thành tác giả?", a: "Bạn chỉ cần đăng ký tài khoản và truy cập mục Studio để bắt đầu biên soạn tài liệu đầu tiên." },
    { q: "dl là gì?", a: "dl là đơn vị tích lũy trong hệ thống, dùng để mua các tài liệu." },
    { q: "Cộng tác viên là gì?", a: "Tính năng này cho phép nhiều người cùng tham gia chỉnh sửa và quản lý tài liệu trong Studio." },
  ];

  const filteredFaqs = faqs.filter(f => f.q.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="w-full max-w-[1000px] mx-auto px-6 py-12 md:py-20 font-sans text-[#1D1D1F]">
      <div className="text-center mb-16 space-y-6">
        <h1 className="text-[40px] md:text-[56px] font-semibold tracking-tight leading-tight">Trung tâm hỗ trợ</h1>
        <p className="text-[17px] text-[#6E6E73] max-w-xl mx-auto leading-relaxed">Giải đáp các thắc mắc về trải nghiệm sử dụng hệ thống DocLib.</p>
        <div className="relative max-w-md mx-auto mt-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
          <input type="text" placeholder="Tìm kiếm câu hỏi..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full h-14 pl-12 pr-4 bg-[#F5F5F7] rounded-full text-[15px] font-medium focus:outline-none focus:bg-[#E8E8ED] transition-colors" />
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-16">
        {[
          { icon: Book, title: "Hướng dẫn đọc", desc: "Sử dụng trình đọc và quản lý thư viện cá nhân", color: "text-[#0071E3]", bg: "bg-[#0071E3]/10" },
          { icon: LifeBuoy, title: "Studio & xuất bản", desc: "Đăng tài liệu, thiết lập giá và quản lý thu nhập", color: "text-[#FF9500]", bg: "bg-[#FF9500]/10" },
          { icon: Shield, title: "Tài khoản & ví", desc: "Bảo mật thông tin, đơn vị dl và các giao dịch", color: "text-[#34C759]", bg: "bg-[#34C759]/10" },
        ].map((item, idx) => (
          <div key={idx} className="p-8 bg-[#F5F5F7] rounded-[24px] border-[#E8E8ED] hover: transition-shadow cursor-pointer">
            <div className={`w-12 h-12 rounded-[14px] flex items-center justify-center mb-6 ${item.bg}`}><item.icon className={`w-6 h-6 ${item.color}`} /></div>
            <h3 className="text-[17px] font-medium text-[#1D1D1F] mb-2">{item.title}</h3>
            <p className="text-[14px] text-[#6E6E73] leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] border-b border-[#E8E8ED] ">Câu hỏi thường gặp</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredFaqs.map((faq, i) => (
            <div key={i} className="p-6 bg-[#F5F5F7] rounded-[24px] hover:bg-[#E8E8ED] transition-colors">
              <h4 className="text-[15px] font-semibold text-[#1D1D1F] mb-3 flex items-start gap-3"><HelpCircle className="w-5 h-5 text-[#0071E3] shrink-0 mt-0.5" />{faq.q}</h4>
              <p className="text-[14px] text-[#6E6E73] leading-relaxed ml-8">{faq.a}</p>
            </div>
          ))}
          {filteredFaqs.length === 0 && <div className="col-span-full py-16 text-center text-[#6E6E73] text-[15px]">Không tìm thấy kết quả phù hợp.</div>}
        </div>
      </div>

      <div className="mt-20 p-12 bg-[#F5F5F7] rounded-[32px] text-center border border-[#E8E8ED]">
        <div className="w-16 h-16 bg-white rounded-[16px] shadow-sm flex items-center justify-center mx-auto mb-6"><MessageCircle className="w-8 h-8 text-[#1D1D1F]" /></div>
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-2">Cần thêm thông tin?</h2>
        <p className="text-[15px] text-[#6E6E73] mb-8">Liên hệ với chúng tôi để được giải đáp thắc mắc trực tiếp.</p>
        <button className="pill-button bg-[#1D1D1F] text-white hover:bg-[#333336]">Gửi yêu cầu hỗ trợ</button>
      </div>
    </div>
  );
}
