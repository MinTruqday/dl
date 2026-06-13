"use client";

import React, { useEffect, useState } from "react";
import { ShieldCheck, FileText, Lock, Scale } from "lucide-react";

export default function TermsPage() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

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
        "Các giao dịch sử dụng Coin (Đ) là cuối cùng và không thể hoàn lại, trừ các trường hợp đặc biệt theo quy định của pháp luật hoặc sai sót hệ thống được xác nhận.",
    },
    {
      title: "4. Quyền riêng tư",
      content:
        "Chúng tôi cam kết bảo mật thông tin cá nhân của bạn và chỉ sử dụng cho mục đích cải thiện trải nghiệm người dùng. Thông tin của bạn sẽ không bao giờ được bán cho bên thứ ba.",
    },
  ];

  return (
    <>
      <div
        className="max-w-3xl mx-auto px-4 py-12 md:py-20 animate-in fade-in slide-in-from-bottom-8 duration-300"
      >
        <div className="mb-16 border-b border-zinc-200 pb-12">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-black mb-4">
            Điều khoản & chính sách
          </h1>
          <p className="text-sm font-bold text-zinc-400">
            Cập nhật lần cuối: 28 tháng 04, 2026
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
          <div className="flex flex-col items-center p-4 bg-white border border-zinc-200 rounded-sm">
            <FileText className="w-5 h-5 mb-2 text-black" />
            <span className="text-[10px] font-bold text-zinc-500">
              Điều khoản
            </span>
          </div>
          <div className="flex flex-col items-center p-4 bg-white border border-zinc-200 rounded-sm">
            <Lock className="w-5 h-5 mb-2 text-black" />
            <span className="text-[10px] font-bold text-zinc-500">Bảo mật</span>
          </div>
          <div className="flex flex-col items-center p-4 bg-white border border-zinc-200 rounded-sm">
            <Scale className="w-5 h-5 mb-2 text-black" />
            <span className="text-[10px] font-bold text-zinc-500">Pháp lý</span>
          </div>
          <div className="flex flex-col items-center p-4 bg-white border border-zinc-200 rounded-sm">
            <ShieldCheck className="w-5 h-5 mb-2 text-black" />
            <span className="text-[10px] font-bold text-zinc-500">
              Bản quyền
            </span>
          </div>
        </div>

        <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
          {sections.map((section, i) => (
            <section key={i} className="space-y-4">
              <h2 className="text-xl font-bold text-black border-l-4 border-black pl-4">
                {section.title}
              </h2>
              <p className="text-zinc-600 leading-relaxed font-medium">
                {section.content}
              </p>
            </section>
          ))}
        </div>

        <div className="mt-20 pt-8 border-t border-zinc-200 text-center">
          <p className="text-sm text-zinc-400 font-medium">
            Nếu bạn có bất kỳ thắc mắc nào về các điều khoản này, vui lòng{" "}
            <a href="/help" className="text-black font-bold ">
              liên hệ với chúng tôi
            </a>
            .
          </p>
        </div>
      </div>
    </>
  );
}
