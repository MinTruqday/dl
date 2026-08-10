import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="border-b border-border bg-surface">
        <nav
          className="mx-auto flex h-[60px] max-w-[1280px] items-center px-4 md:px-8"
          aria-label="Điều hướng trang chủ"
        >
          <Link
            href="/"
            className="flex min-h-11 items-center text-[19px] font-semibold tracking-[-0.035em]"
          >
            DocLib
          </Link>
          <form
            action="/tim-kiem"
            className="ml-8 hidden w-full max-w-[420px] md:block"
          >
            <label htmlFor="home-search" className="sr-only">
              Tìm kiếm toàn DocLib
            </label>
            <input
              id="home-search"
              name="q"
              type="search"
              className="apple-input h-10 w-full bg-surface-quiet"
              placeholder="Tìm kiếm toàn DocLib"
              autoComplete="off"
            />
          </form>
          <div className="ml-auto flex items-center gap-1 sm:gap-2">
            <Link
              href="/dang-nhap"
              className="flex min-h-11 items-center rounded-control px-3 py-2 text-[14px] font-semibold hover:bg-surface-quiet"
            >
              Đăng nhập
            </Link>
            <Link href="/dang-ky" className="pill-button min-h-11 px-4 py-2">
              Đăng ký
            </Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto grid min-h-[calc(100dvh-60px)] max-w-[1280px] lg:grid-cols-[minmax(360px,0.78fr)_minmax(0,1.22fr)]">
        <section className="flex flex-col justify-center px-4 py-10 md:px-8 lg:border-r lg:border-border lg:py-16">
          <h1 className="max-w-[15ch] text-balance text-[38px] font-semibold leading-[1.08] tracking-[-0.045em] md:text-[46px]">
            Đọc, soạn thảo và quản lý tài liệu
          </h1>
          <p className="mt-4 max-w-[46ch] text-[16px] leading-relaxed text-ink-muted md:text-[17px]">
            DocLib kết nối thư viện số, trình soạn thảo, cộng tác và trợ lý AI
            trong cùng một không gian làm việc.
          </p>

          <div className="mt-8 flex flex-wrap gap-2">
            <Link href="/kham-pha" className="pill-button min-h-11 px-5">
              Khám phá tài liệu
            </Link>
            <Link
              href="/soan-thao/khoi-tao"
              className="pill-button-secondary min-h-11 px-5"
            >
              Bắt đầu soạn thảo
            </Link>
          </div>

          <div className="mt-8 flex items-center gap-1 text-[13px] text-ink-muted">
            <Link
              href="/dieu-khoan"
              className="flex min-h-11 items-center rounded-control px-2 hover:text-ink"
            >
              Điều khoản
            </Link>
            <Link
              href="/tro-giup"
              className="flex min-h-11 items-center border-l border-border px-3 hover:text-ink"
            >
              Trợ giúp
            </Link>
          </div>
        </section>

        <section className="flex items-center bg-surface-quiet p-4 md:p-8 lg:p-12">
          <div className="w-full overflow-hidden rounded-workspace border border-border bg-surface shadow-[0_18px_55px_rgba(48,47,42,0.1)]">
            <div className="grid min-h-[420px] grid-cols-[148px_minmax(0,1fr)] md:min-h-[500px] md:grid-cols-[180px_minmax(0,1fr)]">
              <aside className="border-r border-border bg-surface-raised p-3 md:p-4">
                <p className="text-[13px] font-semibold text-ink">Không gian tài liệu</p>
                <div className="mt-5 space-y-1 text-[12px] text-ink-muted">
                  <p className="rounded-control bg-brand-soft px-3 py-2 font-semibold text-brand">Tất cả tài liệu</p>
                  <p className="px-3 py-2">Bản thảo</p>
                  <p className="px-3 py-2">Được chia sẻ</p>
                  <p className="px-3 py-2">Yêu thích</p>
                </div>
              </aside>
              <div className="min-w-0 p-4 md:p-6">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <p className="text-[18px] font-semibold tracking-[-0.025em] text-ink">Tài liệu của bạn</p>
                    <p className="mt-1 text-[12px] text-ink-muted">Đọc, viết và cộng tác trong một nơi</p>
                  </div>
                  <span className="rounded-full bg-brand px-3 py-2 text-[12px] font-semibold text-white">Tạo tài liệu</span>
                </div>
                <div className="divide-y divide-border">
                  {[
                    ["Đề cương nghiên cứu", "Đang chỉnh sửa"],
                    ["Tổng hợp tài liệu tham khảo", "Được chia sẻ"],
                    ["Ghi chú học thuật", "Cập nhật hôm nay"],
                  ].map(([title, meta]) => (
                    <div key={title} className="flex items-center gap-3 py-4">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-control border border-border bg-surface-quiet text-[11px] font-semibold text-brand">DOC</span>
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold text-ink">{title}</p>
                        <p className="mt-0.5 text-[11px] text-ink-muted">{meta}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 border-t border-border pt-4">
                  <p className="text-[12px] font-semibold text-ink">Trợ lý DocLib</p>
                  <div className="mt-2 rounded-panel bg-surface-quiet p-3 text-[12px] leading-relaxed text-ink-muted">
                    Tóm tắt, tìm nguồn và hỗ trợ soạn thảo ngay trên tài liệu đang mở.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
