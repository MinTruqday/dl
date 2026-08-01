"use client";

import React, { useState } from "react";
import {
  HelpCircle,
  Book,
  MessageCircle,
  Shield,
  LifeBuoy,
  Search,
} from "lucide-react";

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");

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
    <div className="w-full h-full font-sans text-ink">
      <div className="text-center mb-16 space-y-6">
        <h1 className="text-[28px] md:text-[32px] font-semibold tracking-tight leading-tight">
          Trung tâm hỗ trợ
        </h1>
        <p className="text-[17px] text-ink-muted max-w-xl mx-auto leading-relaxed">
          Giải đáp các thắc mắc về trải nghiệm sử dụng hệ thống DocLib.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-16">
        {[
          {
            icon: Book,
            title: "Hướng dẫn đọc",
            desc: "Sử dụng trình đọc và quản lý thư viện cá nhân",
            color: "text-brand",
            bg: "bg-brand/10",
          },
          {
            icon: LifeBuoy,
            title: "Studio & xuất bản",
            desc: "Đăng tài liệu, thiết lập giá và quản lý thu nhập",
            color: "text-warning",
            bg: "bg-warning/10",
          },
          {
            icon: Shield,
            title: "Tài khoản & ví",
            desc: "Bảo mật thông tin, đơn vị dl và các giao dịch",
            color: "text-brand",
            bg: "bg-brand/10",
          },
        ].map((item, idx) => (
          <div
            key={idx}
            className="p-8 bg-surface-quiet rounded-panel border border-border hover: transition- cursor-pointer"
          >
            <div
              className={`w-12 h-12 rounded-control flex items-center justify-center mb-6 ${item.bg}`}
            >
              <item.icon className={`w-6 h-6 ${item.color}`} />
            </div>
            <p className="text-[13px] font-medium text-ink-muted mb-2">
              {item.title}
            </p>
            <p className="text-[14px] text-ink-muted leading-relaxed">
              {item.desc}
            </p>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        <h2 className="text-[20px] font-semibold text-ink mb-4">
          Câu hỏi thường gặp
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredFaqs.map((faq, i) => (
            <div
              key={i}
              className="p-6 bg-surface-quiet rounded-panel hover:bg-border transition-colors"
            >
              <h4 className="text-[15px] font-semibold text-ink mb-3 flex items-start gap-3">
                <HelpCircle className="w-5 h-5 text-brand shrink-0 mt-0.5" />
                {faq.q}
              </h4>
              <p className="text-[14px] text-ink-muted leading-relaxed ml-8">
                {faq.a}
              </p>
            </div>
          ))}
          {filteredFaqs.length === 0 && (
            <div className="col-span-full py-16 text-center text-ink-muted text-[15px]">
              Không tìm thấy kết quả phù hợp.
            </div>
          )}
        </div>
      </div>

      <div className="mt-20 p-12 bg-surface-quiet rounded-workspace text-center ">
        <div className="w-16 h-16 bg-white rounded-panel flex items-center justify-center mx-auto mb-6">
          <MessageCircle className="w-8 h-8 text-ink" />
        </div>
        <p className="text-[13px] font-medium text-ink-muted mb-2">
          Cần thêm thông tin?
        </p>
        <p className="text-[15px] text-ink-muted mb-8">
          Liên hệ với chúng tôi để được giải đáp thắc mắc trực tiếp.
        </p>
        <button className="pill-button bg-ink text-white hover:bg-ink">
          Gửi yêu cầu hỗ trợ
        </button>
      </div>
    </div>
  );
}
