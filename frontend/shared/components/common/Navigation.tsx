"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useAnnouncements } from "@/shared/contexts/AnnouncementContext";
import { MenuGroups } from "./Dock";

export default function Navigation() {
  const router = useRouter();
  const { user, logoutState } = useAuth() as any;
  const { unreadCount } = useAnnouncements();
  const [query, setQuery] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const accountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (
        accountRef.current &&
        !accountRef.current.contains(event.target as Node)
      ) {
        setAccountOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  useEffect(() => {
    if (!mobileOpen) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", close);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", close);
    };
  }, [mobileOpen]);

  const search = (event: FormEvent) => {
    event.preventDefault();
    const value = query.trim();
    if (!value) return;
    router.push(`/tim-kiem?q=${encodeURIComponent(value)}`);
  };

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-40 h-[var(--topbar-height)] border-b border-[var(--border)] bg-[color:rgba(255,255,255,0.94)] backdrop-blur-xl">
        <div className="flex h-full items-center gap-4 px-4 lg:px-5">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="min-h-10 rounded-[var(--radius-control)] px-3 text-[14px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)] lg:hidden"
          >
            Menu
          </button>

          <Link
            href="/kham-pha"
            className="w-auto shrink-0 text-[17px] font-semibold tracking-[-0.02em] text-[var(--ink)] lg:w-[calc(var(--sidebar-width)-20px)]"
          >
            DocLib
          </Link>

          <form
            onSubmit={search}
            role="search"
            className="mx-auto hidden w-full max-w-[560px] md:block"
          >
            <label htmlFor="global-search" className="sr-only">
              Tìm trong DocLib
            </label>
            <input
              id="global-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tìm tài liệu và tác giả"
              className="h-10 w-full rounded-[var(--radius-control)] border border-transparent bg-[var(--surface-quiet)] px-4 text-[14px] text-[var(--ink)] outline-none transition focus:border-[var(--brand)] focus:bg-[var(--surface)] focus:ring-2 focus:ring-[var(--brand-soft)]"
            />
          </form>

          <div className="ml-auto flex items-center gap-1">
            {user ? (
              <>
                <Link
                  href="/thong-bao"
                  className="min-h-10 rounded-[var(--radius-control)] px-3 py-2 text-[14px] text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]"
                >
                  Thông báo{unreadCount > 0 ? ` ${unreadCount}` : ""}
                </Link>

                <div ref={accountRef} className="relative">
                  <button
                    type="button"
                    onClick={() => setAccountOpen((value) => !value)}
                    aria-expanded={accountOpen}
                    className="flex min-h-10 items-center gap-2 rounded-[var(--radius-control)] px-2 text-[14px] hover:bg-[var(--surface-quiet)]"
                  >
                    <span className="flex size-7 items-center justify-center overflow-hidden rounded-full bg-[var(--brand)] text-[12px] font-semibold text-white">
                      {user.avatar_url ? (
                        <img
                          src={user.avatar_url}
                          alt=""
                          className="size-full object-cover"
                        />
                      ) : (
                        String(user.full_name || user.username || "D").charAt(0)
                      )}
                    </span>
                    <span className="hidden max-w-32 truncate sm:block">
                      {user.full_name || user.username}
                    </span>
                  </button>

                  {accountOpen && (
                    <div className="absolute right-0 mt-2 w-60 rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[0_18px_50px_rgba(32,32,30,0.12)]">
                      <div className="px-3 py-2">
                        <p className="truncate text-[14px] font-semibold text-[var(--ink)]">
                          {user.full_name || user.username}
                        </p>
                        <p className="truncate text-[12px] text-[var(--ink-muted)]">
                          {user.email}
                        </p>
                      </div>
                      <div className="my-1 h-px bg-[var(--border)]" />
                      <Link
                        href="/ho-so"
                        onClick={() => setAccountOpen(false)}
                        className="block rounded-[var(--radius-control)] px-3 py-2 text-[14px] hover:bg-[var(--surface-quiet)]"
                      >
                        Hồ sơ
                      </Link>
                      <Link
                        href="/cai-dat"
                        onClick={() => setAccountOpen(false)}
                        className="block rounded-[var(--radius-control)] px-3 py-2 text-[14px] hover:bg-[var(--surface-quiet)]"
                      >
                        Cài đặt
                      </Link>
                      <button
                        type="button"
                        onClick={logoutState}
                        className="block w-full rounded-[var(--radius-control)] px-3 py-2 text-left text-[14px] text-[var(--danger)] hover:bg-[var(--danger-soft)]"
                      >
                        Đăng xuất
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <Link
                  href="/dang-nhap"
                  className="min-h-10 rounded-[var(--radius-control)] px-3 py-2 text-[14px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)]"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/dang-ky"
                  className="hidden min-h-10 rounded-[var(--radius-control)] bg-[var(--brand)] px-4 py-2 text-[14px] font-semibold text-white hover:bg-[var(--brand-hover)] sm:block"
                >
                  Tạo tài khoản
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-[color:rgba(32,32,30,0.32)] lg:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Điều hướng"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setMobileOpen(false);
          }}
        >
          <div className="h-full w-[min(88vw,340px)] overflow-y-auto bg-[var(--surface)] p-4 shadow-[20px_0_60px_rgba(32,32,30,0.14)]">
            <div className="mb-6 flex h-10 items-center justify-between">
              <span className="text-[17px] font-semibold">DocLib</span>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="min-h-10 rounded-[var(--radius-control)] px-3 text-[14px] hover:bg-[var(--surface-quiet)]"
              >
                Đóng
              </button>
            </div>
            <nav aria-label="Điều hướng di động">
              <MenuGroups onNavigate={() => setMobileOpen(false)} />
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
