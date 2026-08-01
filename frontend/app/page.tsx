import Image from "next/image";
import Link from "next/link";
import { ArrowRight, Check, FileText, MessageSquareText, Search } from "lucide-react";

const capabilities = [
  {
    title: "Tìm đúng tài liệu",
    description: "Tìm kiếm theo nội dung, chủ đề và mối liên hệ thay vì chỉ dựa vào tên tệp",
    icon: Search,
  },
  {
    title: "Làm việc cùng nhau",
    description: "Giao việc, bình luận và theo dõi phiên bản ngay cạnh tài liệu đang xử lý",
    icon: MessageSquareText,
  },
  {
    title: "Giữ một nguồn dữ liệu",
    description: "Bản thảo, tài liệu đã xuất bản và tệp lưu trữ nằm trong cùng một không gian",
    icon: FileText,
  },
];

const PrimaryCapabilityIcon = capabilities[0].icon;

export default function HomePage() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="sticky top-0 z-30 border-b border-border bg-canvas/95 backdrop-blur-md">
        <nav className="mx-auto flex h-16 max-w-[1280px] items-center px-4 md:px-8" aria-label="Điều hướng trang chủ">
          <Link href="/" className="text-[20px] font-semibold tracking-[-0.04em]">DocLib</Link>
          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <Link href="/kham-pha" className="hidden rounded-control px-3 py-2 text-[14px] font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink sm:block">
              Khám phá
            </Link>
            <Link href="/dang-nhap" className="rounded-control px-3 py-2 text-[14px] font-semibold hover:bg-surface-quiet">
              Đăng nhập
            </Link>
            <Link href="/dang-ky" className="rounded-control bg-brand px-4 py-2 text-[14px] font-semibold text-white transition hover:bg-brand-hover active:translate-y-px">
              Đăng ký
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid min-h-[calc(100dvh-64px)] max-w-[1280px] items-center gap-10 px-4 py-12 md:px-8 lg:grid-cols-[0.82fr_1.18fr] lg:gap-16 lg:py-16">
          <div className="max-w-[560px]">
            <h1 className="text-balance text-[40px] font-semibold leading-[1.08] tracking-[-0.045em] text-ink sm:text-[46px] lg:text-[52px]">
              Tài liệu, công việc và trao đổi trong một nơi
            </h1>
            <p className="mt-6 max-w-[46ch] text-[17px] leading-relaxed text-ink-muted">
              DocLib giúp bạn đọc, quản lý và cộng tác trên tài liệu mà không phải chuyển qua nhiều công cụ
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/dang-ky" className="inline-flex min-h-11 items-center gap-2 rounded-control bg-brand px-5 py-2.5 text-[15px] font-semibold text-white transition hover:bg-brand-hover active:translate-y-px">
                Tạo tài khoản
                <ArrowRight aria-hidden="true" size={18} strokeWidth={1.75} />
              </Link>
              <Link href="/kham-pha" className="inline-flex min-h-11 items-center rounded-control border border-border-strong bg-surface px-5 py-2.5 text-[15px] font-semibold transition hover:bg-surface-quiet active:translate-y-px">
                Xem tài liệu
              </Link>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-workspace bg-surface shadow-[0_24px_70px_rgba(48,47,42,0.13)]">
            <Image
              src="/images/doclib-document-workspace.png"
              alt="Người dùng đang sắp xếp tài liệu trong không gian làm việc"
              width={1536}
              height={1024}
              priority
              sizes="(max-width: 1024px) 100vw, 58vw"
              className="aspect-[3/2] h-full w-full object-cover"
            />
          </div>
        </section>

        <section className="border-y border-border bg-surface">
          <div className="mx-auto grid max-w-[1280px] gap-0 px-4 md:grid-cols-[1.3fr_0.7fr] md:px-8">
            <div className="py-16 md:pr-16 lg:py-24">
              <h2 className="max-w-[700px] text-[28px] font-semibold leading-tight tracking-[-0.035em] md:text-[36px]">
                Nội dung luôn ở vị trí chính
              </h2>
              <p className="mt-5 max-w-[58ch] text-[17px] leading-relaxed text-ink-muted">
                Điều hướng gọn, phản hồi rõ và các công cụ chỉ xuất hiện khi bạn cần dùng
              </p>
            </div>
            <div className="border-t border-border py-10 md:border-l md:border-t-0 md:py-16 md:pl-12 lg:py-24">
              <div className="space-y-5">
                {["Đọc và ghi chú", "Soạn thảo và xuất bản", "Phân quyền và lưu trữ"].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-[15px] font-semibold">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-soft text-brand">
                      <Check aria-hidden="true" size={15} strokeWidth={2} />
                    </span>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1280px] px-4 py-20 md:px-8 lg:py-28">
          <h2 className="max-w-[680px] text-[28px] font-semibold leading-tight tracking-[-0.035em] md:text-[36px]">
            Một luồng làm việc liền mạch
          </h2>
          <div className="mt-12 grid gap-0 overflow-hidden rounded-workspace border border-border bg-surface md:grid-cols-[1.2fr_0.8fr]">
            <div className="border-b border-border p-6 md:border-b-0 md:border-r md:p-10">
              <PrimaryCapabilityIcon aria-hidden="true" size={24} strokeWidth={1.75} className="text-brand" />
              <h3 className="mt-12 text-[24px] font-semibold tracking-[-0.025em]">{capabilities[0].title}</h3>
              <p className="mt-3 max-w-[48ch] text-[15px] leading-relaxed text-ink-muted">{capabilities[0].description}</p>
            </div>
            <div className="divide-y divide-border">
              {capabilities.slice(1).map((item) => (
                <div key={item.title} className="p-6 md:p-8">
                  <item.icon aria-hidden="true" size={22} strokeWidth={1.75} className="text-brand" />
                  <h3 className="mt-8 text-[20px] font-semibold tracking-[-0.02em]">{item.title}</h3>
                  <p className="mt-2 text-[14px] leading-relaxed text-ink-muted">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-brand text-white">
          <div className="mx-auto flex max-w-[1280px] flex-col items-start justify-between gap-8 px-4 py-16 md:flex-row md:items-center md:px-8 lg:py-20">
            <div>
              <h2 className="text-[28px] font-semibold tracking-[-0.03em] md:text-[34px]">Bắt đầu với tài liệu của bạn</h2>
              <p className="mt-3 text-[16px] text-white/75">Tạo tài khoản và mở không gian làm việc đầu tiên</p>
            </div>
            <Link href="/dang-ky" className="inline-flex min-h-11 items-center gap-2 rounded-control bg-white px-5 py-2.5 text-[15px] font-semibold text-brand transition hover:bg-brand-soft active:translate-y-px">
              Tạo tài khoản
              <ArrowRight aria-hidden="true" size={18} strokeWidth={1.75} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-4 px-4 py-8 text-[13px] text-ink-muted sm:flex-row sm:items-center sm:justify-between md:px-8">
          <span className="font-semibold text-ink">DocLib</span>
          <div className="flex gap-5">
            <Link href="/dieu-khoan" className="hover:text-ink">Điều khoản</Link>
            <Link href="/tro-giup" className="hover:text-ink">Trợ giúp</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
