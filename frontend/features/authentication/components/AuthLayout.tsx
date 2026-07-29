import Link from "next/link";

export default function AuthLayout({
  title,
  children,
  footer,
}: {
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="min-h-[100dvh] bg-[var(--canvas)] px-4 py-8 sm:py-12">
      <div className="mx-auto w-full max-w-[440px]">
        <Link
          href="/"
          className="inline-flex min-h-10 items-center text-[17px] font-semibold tracking-[-0.02em] text-[var(--ink)]"
        >
          DocLib
        </Link>
        <section className="mt-12 rounded-[var(--radius-workspace)] border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8">
          <h1 className="text-[28px] font-semibold tracking-[-0.035em] text-[var(--ink)]">
            {title}
          </h1>
          <div className="mt-7">{children}</div>
          {footer && (
            <div className="mt-7 border-t border-[var(--border)] pt-6 text-center text-[14px] text-[var(--ink-muted)]">
              {footer}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
