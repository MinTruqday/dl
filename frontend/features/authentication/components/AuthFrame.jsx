import Link from "next/link";
import Image from "next/image";
export default function AuthFrame({ title, description, children, footer, width = "sm" }) {
  return (
    <main className="min-h-[100dvh] bg-[#eef3ef] px-4 py-5 sm:px-6 md:px-10 md:py-8">
      <div className="mx-auto flex w-full max-w-[1180px] items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-3 text-[19px] font-semibold tracking-[-0.035em] text-ink"
        >
          <Image src="/veriq-logo.png" alt="Veriq" width={36} height={36} className="h-9 w-9 rounded-xl object-cover" priority />
          <span>Veriq</span>
        </Link>
        <Link
          href="/"
          className="rounded-control px-3 py-2 text-[14px] font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink"
        >
          Về trang chủ
        </Link>
      </div>
      <div className="mx-auto grid min-h-[calc(100dvh-104px)] w-full max-w-[1180px] items-center gap-8 py-8 lg:grid-cols-[minmax(0,1fr)_minmax(420px,500px)] lg:gap-16">
        <section className="hidden max-w-xl lg:block">
          <h2 className="text-[28px] font-semibold tracking-[-0.035em] text-ink">
            Chức năng chính
          </h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {[
              "Quản lý yêu cầu và phiên bản",
              "Thiết kế ca kiểm thử",
              "Theo dõi truy vết và độ phủ",
              "Quản lý thay đổi và lỗi",
            ].map((label) => (
              <div key={label} className="rounded-2xl border border-brand/10 bg-white/70 p-4">
                <p className="text-[14px] font-semibold leading-6 text-ink">{label}</p>
              </div>
            ))}
          </div>
        </section>
        <section
          className={`w-full ${width === "md" ? "max-w-[520px]" : "max-w-[500px]"} justify-self-center rounded-3xl border border-border bg-surface p-6 shadow-[0_24px_70px_rgba(48,47,42,0.12)] sm:p-9 lg:justify-self-end`}
        >
          <header className="mb-6">
            <h1 className="text-[28px] font-semibold leading-tight tracking-[-0.035em] text-ink">
              {title}
            </h1>
            {description && (
              <p className="mt-2 text-[14px] leading-relaxed text-ink-muted">{description}</p>
            )}
          </header>
          {children}
          {footer && (
            <div className="mt-7 border-t border-border pt-5 text-[14px] text-ink-muted">
              {footer}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
