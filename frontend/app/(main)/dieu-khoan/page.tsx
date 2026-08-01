import Link from "next/link";
import PageHeader from "@/app/_components/PageHeader";

const sections = [
  {
    id: "su-dung",
    title: "Sử dụng dịch vụ",
    paragraphs: [
      "Khi tạo tài khoản hoặc sử dụng DocLib bạn đồng ý cung cấp thông tin chính xác và chịu trách nhiệm với hoạt động phát sinh từ tài khoản của mình",
      "Bạn không được dùng dịch vụ để phát tán nội dung trái pháp luật xâm phạm quyền của người khác hoặc can thiệp vào hoạt động của hệ thống",
    ],
  },
  {
    id: "noi-dung",
    title: "Nội dung và bản quyền",
    paragraphs: [
      "Tác giả giữ quyền đối với nội dung do mình đăng tải và chịu trách nhiệm về quyền sử dụng các tài liệu nguồn",
      "Người đọc chỉ được sử dụng tài liệu trong phạm vi giấy phép đi kèm và không được sao chép phân phối hoặc bán lại khi chưa có chấp thuận",
    ],
  },
  {
    id: "thanh-toan",
    title: "Thanh toán",
    paragraphs: [
      "Giao dịch bằng dl được ghi nhận trong lịch sử ví và được xử lý theo mức giá hiển thị tại thời điểm xác nhận",
      "Yêu cầu xử lý giao dịch sai cần được gửi qua trang trợ giúp cùng mã giao dịch để đối chiếu",
    ],
  },
  {
    id: "du-lieu",
    title: "Dữ liệu cá nhân",
    paragraphs: [
      "DocLib sử dụng dữ liệu tài khoản để vận hành xác thực bảo vệ tài liệu và cung cấp các chức năng mà bạn lựa chọn",
      "Bạn có thể thay đổi quyền riêng tư tải dữ liệu liên quan hoặc yêu cầu xóa tài khoản trong phần cài đặt",
    ],
  },
  {
    id: "thay-doi",
    title: "Thay đổi điều khoản",
    paragraphs: [
      "Phiên bản mới có hiệu lực từ ngày được ghi ở đầu trang và thay thế phiên bản trước đó",
      "Nếu thay đổi ảnh hưởng đáng kể đến quyền của người dùng DocLib sẽ thông báo qua tài khoản trước khi áp dụng",
    ],
  },
];

export default function TermsPage() {
  return (
    <div className="w-full">
      <PageHeader title="Điều khoản" meta="Hiệu lực từ 28 tháng 4 2026" />

      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,720px)] lg:items-start">
        <nav
          className="border-y border-border py-2 lg:sticky lg:top-[84px]"
          aria-label="Nội dung điều khoản"
        >
          {sections.map((section, index) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className="grid grid-cols-[24px_1fr] gap-2 border-b border-border py-3 text-[13px] text-ink-muted last:border-b-0 hover:text-ink"
            >
              <span className="text-ink-faint">{index + 1}</span>
              <span className="font-semibold">{section.title}</span>
            </a>
          ))}
        </nav>

        <article className="divide-y divide-border border-t border-border">
          {sections.map((section, index) => (
            <section
              key={section.id}
              id={section.id}
              className="scroll-mt-24 py-7 first:pt-6"
            >
              <div className="grid gap-5 sm:grid-cols-[32px_1fr]">
                <span className="text-[13px] font-semibold text-ink-faint">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <h2 className="text-[17px] font-semibold text-ink">
                    {section.title}
                  </h2>
                  <div className="mt-4 space-y-4">
                    {section.paragraphs.map((paragraph) => (
                      <p
                        key={paragraph}
                        className="text-[15px] leading-7 text-ink-muted"
                      >
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          ))}
        </article>
      </div>

      <div className="mt-10 border-t border-border pt-5 text-[13px] text-ink-muted">
        Cần hỗ trợ về điều khoản
        <Link href="/tro-giup" className="ml-2 font-semibold text-brand">
          Mở trợ giúp
        </Link>
      </div>
    </div>
  );
}
