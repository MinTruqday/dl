import Link from "next/link";
import LandingWorkspace from "@/features/content/components/LandingWorkspace";

const workflows = [
  {
    title: "Soạn thảo",
    body: "Ghi chú và bản thảo dùng chung một trình soạn thảo",
  },
  {
    title: "Cộng tác",
    body: "Bình luận phiên bản và quyền truy cập nằm cạnh tài liệu",
  },
  {
    title: "Xuất bản",
    body: "Tạo bản đọc chia sẻ và thiết lập quyền phân phối",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-[100dvh] bg-[var(--canvas)] text-[var(--ink)]">
      <header className="sticky top-0 z-30 border-b border-[color:rgba(221,220,214,0.8)] bg-[color:rgba(247,246,242,0.9)] backdrop-blur-xl">
        <nav
          aria-label="Điều hướng trang chủ"
          className="mx-auto flex h-16 max-w-[1240px] items-center px-5 sm:px-8"
        >
          <Link
            href="/"
            className="text-[18px] font-semibold tracking-[-0.025em]"
          >
            DocLib
          </Link>
          <div className="ml-auto flex items-center gap-1">
            <Link
              href="/kham-pha"
              className="hidden min-h-10 rounded-[var(--radius-control)] px-3 py-2 text-[14px] text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)] sm:block"
            >
              Khám phá
            </Link>
            <Link
              href="/dang-nhap"
              className="min-h-10 rounded-[var(--radius-control)] px-3 py-2 text-[14px] text-[var(--ink)] hover:bg-[var(--surface-quiet)]"
            >
              Đăng nhập
            </Link>
            <Link
              href="/dang-ky"
              className="min-h-10 rounded-[var(--radius-control)] bg-[var(--brand)] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[var(--brand-hover)]"
            >
              Tạo tài khoản
            </Link>
          </div>
        </nav>
      </header>

      <section className="mx-auto grid min-h-[calc(100dvh-64px)] max-w-[1240px] items-center gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[0.82fr_1.18fr] lg:gap-16 lg:py-20">
        <div className="max-w-[560px]">
          <h1 className="text-[clamp(3rem,6vw,5.6rem)] font-semibold leading-[0.98] tracking-[-0.055em]">
            Không gian tài liệu
          </h1>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/dang-ky"
              className="inline-flex min-h-11 items-center rounded-full bg-[var(--brand)] px-6 text-[15px] font-semibold text-white transition hover:bg-[var(--brand-hover)] active:translate-y-px"
            >
              Bắt đầu viết
            </Link>
            <Link
              href="/kham-pha"
              className="inline-flex min-h-11 items-center rounded-full border border-[var(--border-strong)] bg-[var(--surface)] px-6 text-[15px] font-semibold transition hover:bg-[var(--surface-quiet)] active:translate-y-px"
            >
              Xem thư viện
            </Link>
          </div>
        </div>
        <LandingWorkspace />
      </section>

      <section className="border-y border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto max-w-[1240px] px-5 py-20 sm:px-8 lg:py-28">
          <h2 className="max-w-[760px] text-[clamp(2.2rem,4vw,4rem)] font-semibold leading-[1.05] tracking-[-0.045em]">
            Quy trình tài liệu
          </h2>
          <div className="mt-14 grid gap-0 lg:grid-cols-3">
            {workflows.map((item, index) => (
              <article
                key={item.title}
                className={`py-7 lg:px-8 lg:py-2 ${
                  index > 0
                    ? "border-t border-[var(--border)] lg:border-l lg:border-t-0"
                    : ""
                }`}
              >
                <h3 className="text-[19px] font-semibold tracking-[-0.02em]">
                  {item.title}
                </h3>
                <p className="mt-3 max-w-[34ch] text-[15px] leading-6 text-[var(--ink-muted)]">
                  {item.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-[1240px] gap-10 px-5 py-20 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start lg:py-32">
        <div className="rounded-[var(--radius-workspace)] bg-[var(--brand)] p-7 text-white sm:p-10 lg:sticky lg:top-24">
          <p className="max-w-[18ch] text-[clamp(2rem,4vw,3.8rem)] font-semibold leading-[1.06] tracking-[-0.045em]">
            Metis
          </p>
          <p className="mt-6 max-w-[45ch] text-[16px] leading-7 text-white/75">
            Làm việc với tài liệu EditorJS và LaTeX ngay trong không gian soạn
            thảo
          </p>
          <Link
            href="/tro-chuyen"
            className="mt-8 inline-flex min-h-11 items-center rounded-full bg-white px-6 text-[15px] font-semibold text-[var(--brand)] hover:bg-[var(--brand-soft)]"
          >
            Mở Metis
          </Link>
        </div>

        <div className="space-y-10 lg:pt-24">
          <article>
            <h3 className="text-[24px] font-semibold tracking-[-0.03em]">
              Xem thay đổi
            </h3>
            <p className="mt-3 max-w-[52ch] text-[16px] leading-7 text-[var(--ink-muted)]">
              Bạn luôn thấy nội dung nào sẽ đổi và quyết định có áp dụng hay
              không
            </p>
          </article>
          <article className="border-t border-[var(--border)] pt-10">
            <h3 className="text-[24px] font-semibold tracking-[-0.03em]">
              Công cụ tài liệu
            </h3>
            <p className="mt-3 max-w-[52ch] text-[16px] leading-7 text-[var(--ink-muted)]">
              Metis dùng công cụ của DocLib để tạo đọc và chỉnh từng khối
              EditorJS hoặc LaTeX
            </p>
          </article>
          <article className="border-t border-[var(--border)] pt-10">
            <h3 className="text-[24px] font-semibold tracking-[-0.03em]">
              Trạng thái thao tác
            </h3>
            <p className="mt-3 max-w-[52ch] text-[16px] leading-7 text-[var(--ink-muted)]">
              Khi một thao tác chưa có handler hệ thống báo rõ thay vì ghi nhận
              thành công
            </p>
          </article>
        </div>
      </section>

      <section className="bg-[var(--surface-quiet)]">
        <div className="mx-auto flex max-w-[1240px] flex-col items-start justify-between gap-8 px-5 py-20 sm:px-8 lg:flex-row lg:items-end lg:py-24">
          <div>
            <h2 className="max-w-[680px] text-[clamp(2.2rem,4vw,4rem)] font-semibold leading-[1.05] tracking-[-0.045em]">
              Tạo tài liệu
            </h2>
          </div>
          <Link
            href="/dang-ky"
            className="inline-flex min-h-11 shrink-0 items-center rounded-full bg-[var(--brand)] px-6 text-[15px] font-semibold text-white hover:bg-[var(--brand-hover)]"
          >
            Tạo không gian
          </Link>
        </div>
      </section>

      <footer className="border-t border-[var(--border)] bg-[var(--surface)]">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-4 px-5 py-8 text-[13px] text-[var(--ink-muted)] sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span className="font-semibold text-[var(--ink)]">DocLib</span>
          <div className="flex gap-5">
            <Link href="/dieu-khoan" className="hover:text-[var(--ink)]">
              Điều khoản
            </Link>
            <Link href="/tro-giup" className="hover:text-[var(--ink)]">
              Trợ giúp
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
