"use client";

import React, { useEffect, useState } from "react";
import {
  HelpCircle,
  Book,
  MessageCircle,
  Shield,
  LifeBuoy,
  Search,
} from "lucide-react";

export default function HelpPage() {
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const faqs = [
    {
      q: "DocLib là gì?",
      a: "DocLib là nền tảng xuất bản và chia sẻ tài liệu trực tuyến, tập trung vào trải nghiệm đọc tối giản và hiệu quả.",
    },
    {
      q: "Làm thế nào để trở thành tác giả?",
      a: "Bạn chỉ cần đăng ký tài khoản và truy cập mục Studio để bắt đầu biên soạn tài liệu đầu tiên.",
    },
    {
      q: "dl là gì?",
      a: "dl là đơn vị tích lũy trong hệ thống, dùng để mua các tài liệu.",
    },
    {
      q: "Cộng tác viên là gì?",
      a: "Tính năng này cho phép nhiều người cùng tham gia chỉnh sửa và quản lý tài liệu trong Studio.",
    },
  ];

  const filteredFaqs = faqs.filter((f) =>
    f.q.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <>
      <div className="max-w-4xl mx-auto px-6 py-12 md:py-20 font-sans ">
        <div className="text-center mb-20 space-y-6">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-black">
            Trung tâm hỗ trợ
          </h1>
          <p className="text-zinc-500 font-medium max-w-xl mx-auto text-sm leading-relaxed">
            Giải đáp các thắc mắc về trải nghiệm sử dụng hệ thống DocLib
          </p>
          <div className="relative max-w-md mx-auto group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 group-focus-within:text-black " />
            <input
              type="text"
              placeholder=""
              className="w-full h-14 pl-12 pr-4 bg-white border border-zinc-200 rounded-xl focus:outline-none focus:border-black focus:bg-white text-sm font-bold"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div
          className="grid md:grid-cols-3 gap-6 mb-20 "
          
        >
          {[
            {
              icon: Book,
              title: "Hướng dẫn đọc",
              desc: "Sử dụng trình đọc và quản lý thư viện cá nhân",
            },
            {
              icon: LifeBuoy,
              title: "Studio & xuất bản",
              desc: "Đăng tài liệu, thiết lập giá và quản lý thu nhập",
            },
            {
              icon: Shield,
              title: "Tài khoản & ví",
              desc: "Bảo mật thông tin, đơn vị dl và các giao dịch",
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-8 border border-zinc-200 rounded-xl group cursor-pointer active:scale-[0.98]"
            >
              <item.icon className="w-8 h-8 mb-6 text-zinc-200 " />
              <h3 className="font-bold text-black mb-3">{item.title}</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-bold">
                {item.desc}
              </p>
            </div>
          ))}
        </div>

        <div
          className="space-y-12 "
          
        >
          <h2 className="text-2xl font-bold text-black border-b border-zinc-100 pb-6 tracking-tight">
            Câu hỏi thường gặp
          </h2>
          <div className="space-y-4">
            {filteredFaqs.map((faq, i) => (
              <div
                key={i}
                className="p-8 bg-white border border-zinc-200 rounded-xl "
              >
                <h4 className="font-bold text-black mb-3 flex items-center gap-3">
                  <HelpCircle className="w-4 h-4 text-zinc-400" />
                  {faq.q}
                </h4>
                <p className="text-sm text-zinc-500 leading-relaxed font-medium">
                  {faq.a}
                </p>
              </div>
            ))}
            {filteredFaqs.length === 0 && (
              <p className="text-center py-20 text-zinc-300 font-bold italic text-sm">
                Không tìm thấy kết quả phù hợp
              </p>
            )}
          </div>
        </div>

        <div className="mt-24 p-12 bg-black text-white rounded-xl text-center animate-in slide-in-from-bottom-8 ">
          <MessageCircle className="w-10 h-10 mx-auto mb-6 text-zinc-400" />
          <h2 className="text-2xl font-bold mb-3 tracking-tight">
            Cần thêm thông tin?
          </h2>
          <p className="text-zinc-400 mb-10 text-[11px] font-bold">
            Liên hệ với chúng tôi để được giải đáp thắc mắc
          </p>
          <button className="px-10 py-4 bg-white text-black font-bold text-[11px] active:scale-95">
            Gửi yêu cầu hỗ trợ
          </button>
        </div>
      </div>
    </>
  );
}
