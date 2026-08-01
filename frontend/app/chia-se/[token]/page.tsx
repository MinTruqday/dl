"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import InlineState from "@/app/_components/InlineState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useSharedStorageItem } from "./useSharedStorageItem";

function formatSize(value: number) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1,
  );
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

export default function SharedStoragePage() {
  const token = String(useParams().token || "");
  const state = useSharedStorageItem(token);
  const [password, setPassword] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await state.open(password);
  };

  return (
    <main className="min-h-[100dvh] bg-canvas px-5 py-8 text-ink">
      <div className="mx-auto max-w-2xl">
        <header className="flex h-12 items-center justify-between border-b border-border">
          <Link href="/" className="text-[19px] font-semibold tracking-[-0.035em]">
            DocLib
          </Link>
          <span className="text-[12px] text-ink-muted">Liên kết bảo vệ</span>
        </header>
        <section className="mt-8 rounded-panel border border-border bg-surface p-6">
          {state.loading ? (
            <PageLoader rows={4} />
          ) : state.error ? (
            <InlineState title="Không thể mở tệp" detail={state.error} tone="danger" />
          ) : state.passwordRequired && !state.item ? (
            <form onSubmit={submit} className="max-w-sm space-y-4">
              <div>
                <label htmlFor="share-access-password" className="mb-2 block text-[13px] font-semibold">
                  Mật khẩu truy cập
                </label>
                <input
                  id="share-access-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="apple-input w-full"
                  autoFocus
                />
              </div>
              <Button type="submit" disabled={!password}>
                Mở tệp
              </Button>
            </form>
          ) : state.item ? (
            <div>
              <p className="text-[12px] font-semibold text-ink-muted">
                {state.item.is_folder ? "Thư mục" : "Tệp"}
              </p>
              <h1 className="mt-2 break-words text-[22px] font-semibold tracking-[-0.02em]">
                {state.item.name}
              </h1>
              <dl className="mt-6 grid gap-4 border-y border-border py-5 text-[13px] sm:grid-cols-2">
                <div>
                  <dt className="text-ink-muted">Dung lượng</dt>
                  <dd className="mt-1 font-semibold">{formatSize(state.item.size)}</dd>
                </div>
                <div>
                  <dt className="text-ink-muted">Cập nhật</dt>
                  <dd className="mt-1 font-semibold">
                    {new Date(state.item.updated_at).toLocaleString("vi-VN")}
                  </dd>
                </div>
              </dl>
              {state.item.download_url && (
                <a
                  href={state.item.download_url}
                  className="mt-6 inline-flex min-h-11 items-center rounded-control border border-brand bg-brand px-4 py-2.5 text-[14px] font-semibold text-white hover:bg-brand-hover"
                >
                  Tải xuống
                </a>
              )}
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
