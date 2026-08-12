"use client";

import { useEffect } from "react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-[100dvh] items-center justify-center bg-canvas px-6 py-12 text-ink">
      <section className="w-full max-w-md rounded-panel border border-border bg-surface p-6 shadow-[0_18px_50px_rgba(48,47,42,0.08)]">
        <p className="text-[12px] font-semibold uppercase tracking-[0.12em] text-danger">
          Có lỗi xảy ra
        </p>
        <h1 className="mt-3 text-[22px] font-semibold tracking-[-0.02em]">
          Không thể hiển thị trang này
        </h1>
        <p className="mt-2 text-[14px] leading-6 text-ink-muted">
          Thử tải lại trang hoặc quay về Khám phá để tiếp tục
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={reset}
            className="min-h-11 rounded-control bg-brand px-4 py-2 text-[14px] font-semibold text-white hover:bg-brand-hover"
          >
            Thử lại
          </button>
          <a
            href="/kham-pha"
            className="inline-flex min-h-11 items-center rounded-control border border-border-strong px-4 py-2 text-[14px] font-semibold text-ink hover:bg-surface-quiet"
          >
            Về Khám phá
          </a>
        </div>
      </section>
    </main>
  );
}
