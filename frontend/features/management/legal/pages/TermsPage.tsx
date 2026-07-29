import Link from "next/link";
import PageHeader from "@/shared/components/common/PageHeader";

const sections = [
  {
    title: "Sử dụng dịch vụ",
    content:
      "Khi sử dụng DocLib, bạn đồng ý tuân thủ các điều kiện trong tài liệu này và các quy định pháp luật có liên quan",
  },
  {
    title: "Quyền sở hữu trí tuệ",
    content:
      "Tác giả giữ quyền sở hữu nội dung đã đăng tải và chịu trách nhiệm về quyền sử dụng tài liệu DocLib cung cấp công cụ lưu trữ, cộng tác và phân phối",
  },
  {
    title: "Thanh toán",
    content:
      "Giao dịch được xử lý theo thông tin hiển thị tại thời điểm xác nhận Trường hợp sai sót hệ thống sẽ được kiểm tra theo lịch sử giao dịch",
  },
  {
    title: "Quyền riêng tư",
    content:
      "Thông tin cá nhân chỉ được sử dụng để vận hành tài khoản, bảo vệ dịch vụ và cải thiện chức năng theo chính sách dữ liệu",
  },
];

export default function TermsPage() {
  return (
    <div className="app-page mx-auto max-w-[840px] gap-8">
      <PageHeader
        title="Điều khoản và chính sách"
        description="Cập nhật ngày 28 tháng 4 năm 2026"
      />
      <div className="surface divide-y divide-[var(--border)] px-6 sm:px-8">
        {sections.map((section, index) => (
          <section className="py-7" key={section.title}>
            <div className="grid gap-3 sm:grid-cols-[32px_1fr]">
              <span className="text-[13px] font-medium text-[var(--ink-faint)]">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h2 className="text-[17px] font-semibold text-[var(--ink)]">
                  {section.title}
                </h2>
                <p className="mt-2 text-[15px] leading-7 text-[var(--ink-muted)]">
                  {section.content}
                </p>
              </div>
            </div>
          </section>
        ))}
      </div>
      <p className="text-[14px] text-[var(--ink-muted)]">
        Cần làm rõ một điều khoản{" "}
        <Link href="/tro-giup" className="font-medium text-[var(--brand)]">
          Liên hệ hỗ trợ
        </Link>
      </p>
    </div>
  );
}
