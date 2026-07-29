"use client";

import React from "react";
import { ShieldCheck, FileText, Lock, Scale } from "lucide-react";

export default function TermsPage() {
  const sections = [
    {
      title: "1. Điều khoản sử dụng",
      content:
        "Bằng cách sử dụng DocLib, bạn đồng ý tuân thủ các quy định và điều kiện được nêu trong tài liệu này. Chúng tôi có quyền thay đổi điều khoản bất cứ lúc nào mà không cần thông báo trước.",
    },
    {
      title: "2. Quyền sở hữu trí tuệ",
      content:
        "Tất cả nội dung được đăng tải bởi Tác giả đều thuộc quyền sở hữu của họ. DocLib chỉ cung cấp nền tảng để phân phối và chia sẻ. Người dùng không được phép sao chép hoặc phát tán trái phép các tài liệu có bản quyền.",
    },
    {
      title: "3. Chính sách thanh toán",
      content:
        "Các giao dịch sử dụng dl là cuối cùng và không thể hoàn lại, trừ các trường hợp đặc biệt theo quy định của pháp luật hoặc sai sót hệ thống được xác nhận.",
    },
    {
      title: "4. Quyền riêng tư",
      content:
        "Chúng tôi cam kết bảo mật thông tin cá nhân của bạn và chỉ sử dụng cho mục đích cải thiện trải nghiệm người dùng. Thông tin của bạn sẽ không bao giờ được bán cho bên thứ ba.",
    },
  ];

  return (
    <div className="w-full max-w-[800px] mx-auto px-6 md:px-0 py-12 md:py-20 font-sans text-[#1D1D1F]">
      <div className="mb-16  pb-12 text-center">
        <h1 className="text-[40px] md:text-[56px] font-semibold tracking-tight text-[#1D1D1F] mb-4">
          Điều khoản & chính sách
        </h1>
        <p className="text-[15px] text-[#6E6E73]">
          Cập nhật lần cuối: 28 tháng 04, 2026
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
        {[
          {
            icon: FileText,
            label: "Điều khoản",
            bg: "bg-[#0071E3]/10",
            color: "text-[#0071E3]",
          },
          {
            icon: Lock,
            label: "Bảo mật",
            bg: "bg-[#34C759]/10",
            color: "text-[#34C759]",
          },
          {
            icon: Scale,
            label: "Pháp lý",
            bg: "bg-[#FF9500]/10",
            color: "text-[#FF9500]",
          },
          {
            icon: ShieldCheck,
            label: "Bản quyền",
            bg: "bg-[#AF52DE]/10",
            color: "text-[#AF52DE]",
          },
        ].map((item, idx) => (
          <div
            key={idx}
            className="flex flex-col items-center p-6 bg-[#F5F5F7] rounded-[18px]"
          >
            <div
              className={`w-12 h-12 rounded-[10px] flex items-center justify-center mb-3 ${item.bg}`}
            >
              <item.icon className={`w-6 h-6 ${item.color}`} />
            </div>
            <span className="text-[14px] font-medium text-[#1D1D1F]">
              {item.label}
            </span>
          </div>
        ))}
      </div>

      <div className="space-y-12">
        {sections.map((section, i) => (
          <section key={i} className="space-y-4">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              {section.title}
            </p>
            <p className="text-[16px] text-[#6E6E73] leading-relaxed">
              {section.content}
            </p>
          </section>
        ))}
      </div>

      <div className="mt-20 pt-8 text-center">
        <p className="text-[15px] text-[#6E6E73]">
          Nếu bạn có bất kỳ thắc mắc nào về các điều khoản này, vui lòng{" "}
          <a
            href="/tro-giup"
            className="text-[#0071E3] hover:underline font-medium"
          >
            liên hệ với chúng tôi
          </a>
          .
        </p>
      </div>
    </div>
  );
}
