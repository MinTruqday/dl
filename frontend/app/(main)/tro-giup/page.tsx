"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import PageHeader from "@/app/_components/PageHeader";

const guides = [
  {
    title: "Đọc và lưu tài liệu",
    detail: "Mở trình đọc, đánh dấu và quản lý tài liệu đã lưu",
    href: "/thu-vien",
  },
  {
    title: "Soạn thảo và xuất bản",
    detail: "Tạo bản thảo, cấu hình quyền truy cập và theo dõi phiên bản",
    href: "/soan-thao",
  },
  {
    title: "Tài khoản và thanh toán",
    detail: "Quản lý hồ sơ, bảo mật, số dư và giao dịch",
    href: "/cai-dat",
  },
];

const faqs = [
  {
    title: "DocLib dùng để làm gì",
    detail:
      "DocLib hỗ trợ đọc, soạn thảo, xuất bản và cộng tác trên tài liệu trong cùng một không gian làm việc",
  },
  {
    title: "Cách tạo tài liệu mới",
    detail:
      "Mở trình soạn thảo, chọn khởi tạo tài liệu và nhập nội dung trước khi cấu hình xuất bản",
  },
  {
    title: "dl được sử dụng ở đâu",
    detail:
      "dl là đơn vị thanh toán trong DocLib, dùng để mua tài liệu và sử dụng các dịch vụ có tính phí",
  },
  {
    title: "Cách mời người cùng biên tập",
    detail:
      "Mở cấu hình của bản thảo, chọn người cộng tác và cấp quyền phù hợp với công việc",
  },
  {
    title: "Cách kiểm tra lịch sử thay đổi",
    detail:
      "Mở lịch sử trong khu vực soạn thảo để xem phiên bản, người thực hiện và thời điểm cập nhật",
  },
  {
    title: "Cách bảo vệ tài khoản",
    detail:
      "Dùng mật khẩu riêng cho DocLib, bật xác thực hai bước và kết thúc các phiên đăng nhập không còn sử dụng",
  },
];

export default function HelpPage() {
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    const value = query.trim().toLocaleLowerCase("vi");
    if (!value) return faqs;
    return faqs.filter((item) =>
      `${item.title} ${item.detail}`.toLocaleLowerCase("vi").includes(value),
    );
  }, [query]);

  return (
    <div className="w-full">
      <PageHeader title="Trợ giúp" />

      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(19rem,0.58fr)]">
        <section aria-labelledby="faq-title">
          <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <h2 id="faq-title" className="text-[18px] font-semibold text-ink">
              Câu hỏi thường gặp
            </h2>
            <div className="w-full sm:max-w-xs">
              <label
                htmlFor="help-search"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Tìm câu trả lời
              </label>
              <input
                id="help-search"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="apple-input w-full"
                placeholder="Nhập nội dung cần tìm"
              />
            </div>
          </div>

          {results.length ? (
            <div className="overflow-hidden rounded-panel border border-border bg-surface">
              {results.map((item) => (
                <details
                  key={item.title}
                  className="group border-b border-border last:border-b-0"
                >
                  <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 font-semibold text-ink hover:bg-surface-raised">
                    <span>{item.title}</span>
                    <span
                      aria-hidden="true"
                      className="text-[18px] font-normal text-ink-muted group-open:rotate-45"
                    >
                      +
                    </span>
                  </summary>
                  <p className="max-w-[70ch] px-4 pb-5 text-[14px] leading-relaxed text-ink-muted">
                    {item.detail}
                  </p>
                </details>
              ))}
            </div>
          ) : (
            <div className="rounded-panel border border-border bg-surface px-5 py-10">
              <p className="font-semibold text-ink">
                Không tìm thấy nội dung phù hợp
              </p>
              <p className="mt-2 text-[14px] text-ink-muted">
                Thử tìm bằng tên tính năng hoặc hành động cần thực hiện
              </p>
            </div>
          )}
        </section>

        <aside aria-labelledby="guide-title">
          <h2
            id="guide-title"
            className="mb-5 text-[18px] font-semibold text-ink"
          >
            Lối tắt hướng dẫn
          </h2>
          <div className="overflow-hidden rounded-panel border border-border bg-surface">
            {guides.map((guide) => (
              <Link
                key={guide.href}
                href={guide.href}
                className="block border-b border-border px-4 py-4 last:border-b-0 hover:bg-surface-raised"
              >
                <p className="font-semibold text-ink">{guide.title}</p>
                <p className="mt-1 text-[13px] leading-relaxed text-ink-muted">
                  {guide.detail}
                </p>
              </Link>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
