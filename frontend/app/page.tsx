import Image from "next/image";
import Link from "next/link";

const entryPoints = [
  {
    href: "/kham-pha",
    title: "Khám phá",
    detail: "Tài liệu công khai theo chủ đề",
  },
  {
    href: "/thu-vien",
    title: "Thư viện",
    detail: "Lịch sử đọc và danh sách đã lưu",
  },
  {
    href: "/soan-thao/khoi-tao",
    title: "Tạo tài liệu",
    detail: "Bắt đầu bản thảo mới",
  },
];

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
            className="text-[19px] font-semibold tracking-[-0.035em]"
          >
            DocLib
          </Link>
          <div className="ml-auto flex items-center gap-1 sm:gap-2">
            <Link
              href="/kham-pha"
              className="rounded-control px-3 py-2 text-[14px] font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
            >
              Khám phá
            </Link>
            <Link
              href="/dang-nhap"
              className="rounded-control px-3 py-2 text-[14px] font-semibold hover:bg-surface-quiet"
            >
              Đăng nhập
            </Link>
            <Link href="/dang-ky" className="pill-button min-h-10 px-4 py-2">
              Đăng ký
            </Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto grid min-h-[calc(100dvh-60px)] max-w-[1280px] lg:grid-cols-[minmax(360px,0.78fr)_minmax(0,1.22fr)]">
        <section className="flex flex-col justify-center px-4 py-10 md:px-8 lg:border-r lg:border-border lg:py-16">
          <h1 className="text-[28px] font-semibold tracking-[-0.03em]">
            DocLib
          </h1>

          <form action="/tim-kiem" className="mt-8">
            <label
              htmlFor="home-search"
              className="text-[14px] font-semibold text-ink"
            >
              Tìm tài liệu
            </label>
            <div className="mt-2 flex gap-2">
              <input
                id="home-search"
                name="q"
                type="search"
                className="apple-input min-w-0 flex-1"
                autoComplete="off"
              />
              <button type="submit" className="pill-button">
                Tìm kiếm
              </button>
            </div>
          </form>

          <nav className="mt-10 border-t border-border" aria-label="Bắt đầu">
            {entryPoints.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group grid grid-cols-[1fr_auto] gap-4 border-b border-border py-4"
              >
                <span>
                  <span className="block text-[15px] font-semibold text-ink group-hover:text-brand">
                    {item.title}
                  </span>
                  <span className="mt-1 block text-[13px] text-ink-muted">
                    {item.detail}
                  </span>
                </span>
                <span className="self-center text-[13px] font-semibold text-ink-faint group-hover:text-brand">
                  Mở
                </span>
              </Link>
            ))}
          </nav>

          <div className="mt-8 flex items-center gap-3 text-[13px] text-ink-muted">
            <Link href="/dieu-khoan" className="hover:text-ink">
              Điều khoản
            </Link>
            <Link
              href="/tro-giup"
              className="border-l border-border pl-3 hover:text-ink"
            >
              Trợ giúp
            </Link>
          </div>
        </section>

        <section className="flex items-center bg-surface-quiet p-4 md:p-8 lg:p-12">
          <div className="w-full overflow-hidden rounded-workspace border border-border bg-surface shadow-[0_18px_55px_rgba(48,47,42,0.1)]">
            <Image
              src="/images/doclib-document-workspace.png"
              alt="Không gian quản lý tài liệu DocLib"
              width={1536}
              height={1024}
              priority
              sizes="(max-width: 1024px) 100vw, 60vw"
              className="aspect-[3/2] h-full w-full object-cover"
            />
          </div>
        </section>
      </main>
    </div>
  );
}
