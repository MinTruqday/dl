import Link from "next/link";
export default function AuthFrame({ title, description, children, footer, width = "sm", }) {
    return (<main className="flex min-h-[100dvh] flex-col bg-canvas px-4 py-6 sm:px-6">
      <div className="mx-auto flex w-full max-w-[1280px] items-center justify-between">
        <Link href="/" className="text-[19px] font-semibold tracking-[-0.035em] text-ink">
          DocLib
        </Link>
        <Link href="/" className="rounded-control px-3 py-2 text-[14px] font-semibold text-ink-muted hover:bg-surface-quiet hover:text-ink">
          Khám phá
        </Link>
      </div>
      <div className="flex flex-1 items-center justify-center py-10">
        <section className={`w-full ${width === "md" ? "max-w-[520px]" : "max-w-[420px]"} rounded-workspace border border-border bg-surface p-6 shadow-[0_20px_60px_rgba(48,47,42,0.08)] sm:p-8`}>
          <header className="mb-6">
            <h1 className="text-[22px] font-semibold leading-tight tracking-[-0.02em] text-ink">
              {title}
            </h1>
            {description && (<p className="mt-2 text-[14px] leading-relaxed text-ink-muted">
                {description}
              </p>)}
          </header>
          {children}
          {footer && (<div className="mt-7 border-t border-border pt-5 text-[14px] text-ink-muted">
              {footer}
            </div>)}
        </section>
      </div>
    </main>);
}
