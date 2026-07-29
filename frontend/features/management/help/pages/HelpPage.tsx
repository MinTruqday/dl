"use client";

import { useState } from "react";
import EmptyState from "@/shared/components/common/EmptyState";
import PageHeader from "@/shared/components/common/PageHeader";

const topics = [
  {
    title: "Đọc và thư viện",
    description: "Trình đọc dấu trang danh sách và lịch sử",
  },
  {
    title: "Soạn thảo và xuất bản",
    description: "Tài liệu cộng tác phiên bản và phân phối",
  },
  {
    title: "Tài khoản và ví",
    description: "Hồ sơ bảo mật số dư và giao dịch",
  },
];

const questions = [
  {
    question: "DocLib dùng để làm gì",
    answer:
      "DocLib hỗ trợ soạn thảo cộng tác quản lý xuất bản và đọc tài liệu",
  },
  {
    question: "Làm thế nào để tạo tài liệu",
    answer: "Mở mục Tài liệu và chọn Tạo tài liệu",
  },
  {
    question: "dl là gì",
    answer: "dl là đơn vị dùng cho giao dịch tài liệu trong DocLib",
  },
  {
    question: "Mời người khác cộng tác như thế nào",
    answer:
      "Mở tài liệu chọn Cộng tác rồi cấp quyền phù hợp cho từng thành viên",
  },
];

export default function HelpPage() {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLocaleLowerCase("vi");
  const filteredQuestions = questions.filter(
    (item) =>
      item.question.toLocaleLowerCase("vi").includes(normalizedQuery) ||
      item.answer.toLocaleLowerCase("vi").includes(normalizedQuery),
  );

  return (
    <div className="app-page gap-8">
      <PageHeader title="Trợ giúp" />
      <label className="max-w-xl">
        <span className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]">
          Tìm câu hỏi
        </span>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="field-control w-full"
        />
      </label>
      <section className="grid gap-3 md:grid-cols-3" aria-label="Chủ đề">
        {topics.map((topic) => (
          <article className="surface p-5" key={topic.title}>
            <h2 className="text-[16px] font-semibold text-[var(--ink)]">
              {topic.title}
            </h2>
            <p className="mt-2 text-[14px] leading-6 text-[var(--ink-muted)]">
              {topic.description}
            </p>
          </article>
        ))}
      </section>
      <section>
        <h2 className="mb-4 text-[17px] font-semibold text-[var(--ink)]">
          Câu hỏi thường gặp
        </h2>
        {filteredQuestions.length > 0 ? (
          <div className="surface divide-y divide-[var(--border)]">
            {filteredQuestions.map((item) => (
              <details className="group px-5 py-4" key={item.question}>
                <summary className="cursor-pointer list-none pr-8 text-[15px] font-medium text-[var(--ink)]">
                  {item.question}
                </summary>
                <p className="mt-3 max-w-[70ch] text-[14px] leading-6 text-[var(--ink-muted)]">
                  {item.answer}
                </p>
              </details>
            ))}
          </div>
        ) : (
          <EmptyState
            compact
            text="Không tìm thấy câu hỏi"
            description="Thử một từ khóa khác"
          />
        )}
      </section>
      <section className="surface flex flex-col items-start gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-[16px] font-semibold text-[var(--ink)]">
            Yêu cầu hỗ trợ
          </h2>
          <p className="mt-1 text-[14px] text-[var(--ink-muted)]">
            Gửi nội dung và thông tin liên hệ cho đội vận hành
          </p>
        </div>
        <button type="button" className="button-secondary shrink-0">
          Gửi yêu cầu
        </button>
      </section>
    </div>
  );
}
