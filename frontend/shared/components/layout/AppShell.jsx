"use client";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Bell, Menu, Search, X } from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useAnnouncements } from "@/shared/contexts/AnnouncementContext";
import { API_URL, authenticatedFetch } from "@/shared/services/api-client";
import { availableNavigation, navigationGroupsFor, projectIdFromPath } from "./navigation";
const fullWidthRoutes = [];
function NavigationList({ onNavigate, projectPermissions }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const groups = useMemo(
    () => availableNavigation(navigationGroupsFor(pathname), user, projectPermissions),
    [pathname, projectPermissions, user],
  );
  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <div key={group.label}>
          <p className="mb-2 px-3 text-[12px] font-semibold text-ink-faint">{group.label}</p>
          <div className="space-y-1">
            {group.items.map((item) => {
              const active =
                pathname === item.href ||
                (item.id !== "dashboard" && pathname.startsWith(`${item.href}/`));
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={`flex min-h-10 items-center gap-3 rounded-control px-3 text-[14px] font-medium transition duration-150 ${
                    active
                      ? "bg-brand-soft text-brand"
                      : "text-ink-muted hover:bg-surface-quiet hover:text-ink"
                  }`}
                >
                  <item.icon aria-hidden="true" size={18} strokeWidth={1.75} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
export default function AppShell({ children, requireAuth }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const routeQuery = searchParams.get("q") || "";
  const projectId = projectIdFromPath(pathname);
  const { user, isLoading, logoutState } = useAuth();
  const { unreadCount } = useAnnouncements();
  const notificationEnabled = process.env.NEXT_PUBLIC_NOTIFICATION_ENABLED === "true";
  const [mobileOpen, setMobileOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState(routeQuery);
  const [projectPermissions, setProjectPermissions] = useState(null);
  const accountRef = useRef(null);
  useEffect(() => {
    setSearchQuery(routeQuery);
  }, [routeQuery]);
  useEffect(() => {
    if (!projectId || !user) {
      setProjectPermissions(null);
      return;
    }
    let active = true;
    authenticatedFetch(`${API_URL}/kiem-thu/du-an/${projectId}`)
      .then(async (response) => {
        if (!response.ok) return [];
        const body = await response.json();
        return body?.data?.current_permissions || [];
      })
      .catch(() => [])
      .then((permissions) => {
        if (active) setProjectPermissions(permissions);
      });
    return () => {
      active = false;
    };
  }, [projectId, user]);
  useEffect(() => {
    if (requireAuth && !isLoading && !user) {
      const query = searchParams.toString();
      const returnPath = `${pathname}${query ? `?${query}` : ""}`;
      router.replace(`/dang-nhap?next=${encodeURIComponent(returnPath)}`);
    }
  }, [isLoading, pathname, requireAuth, router, searchParams, user]);
  useEffect(() => {
    const close = (event) => {
      if (accountRef.current && !accountRef.current.contains(event.target)) setAccountOpen(false);
    };
    const escape = (event) => {
      if (event.key === "Escape") {
        setMobileOpen(false);
        setAccountOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", escape);
    };
  }, []);
  if (requireAuth && (isLoading || !user)) {
    return (
      <div className="mx-auto flex min-h-[100dvh] w-full max-w-[1280px] gap-8 px-6 py-10">
        <div className="hidden w-48 space-y-3 lg:block">
          <div className="skeleton h-7 w-24" />
          <div className="skeleton mt-10 h-10 w-full" />
          <div className="skeleton h-10 w-full" />
          <div className="skeleton h-10 w-4/5" />
        </div>
        <div className="flex-1 space-y-5">
          <div className="skeleton h-9 w-52" />
          <div className="skeleton h-4 w-80 max-w-full" />
          <div className="skeleton mt-10 h-56 w-full" />
        </div>
      </div>
    );
  }
  const fullWidth =
    pathname.startsWith("/soan-thao/chinh-sua") ||
    fullWidthRoutes.some((route) => pathname.startsWith(route));
  const initials = String(user?.full_name || user?.username || "D")
    .trim()
    .charAt(0)
    .toUpperCase();
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <a
        href="#main-content"
        className="fixed left-3 top-3 z-[60] -translate-y-20 rounded-control bg-brand px-4 py-2 text-[14px] font-semibold text-white transition focus:translate-y-0"
      >
        Bỏ qua điều hướng
      </a>
      <header className="fixed inset-x-0 top-0 z-40 h-[68px] border-b border-border bg-surface/95 backdrop-blur-md lg:left-[260px]">
        <div className="flex h-full items-center gap-3 px-4 md:px-6">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="flex h-11 w-11 items-center justify-center rounded-control text-ink-muted hover:bg-surface-quiet lg:hidden"
            aria-label="Mở điều hướng"
          >
            <Menu size={20} strokeWidth={1.75} />
          </button>
          <Link
            href={projectId ? `/qa/projects/${projectId}` : "/qa/projects"}
            className="flex items-center gap-2 lg:hidden"
          >
            <Image
              src="/brand/veriq-logo.png"
              alt="Veriq"
              width={32}
              height={32}
              className="h-8 w-8 rounded-lg object-cover"
              priority
            />
            <span className="text-[15px] font-bold tracking-[-0.02em]">Veriq</span>
          </Link>
          {projectId && (
            <form
              action={`/qa/projects/${projectId}/knowledge`}
              className="relative hidden w-full max-w-[520px] md:block"
            >
              <button
                type="submit"
                aria-label="Thực hiện tìm kiếm"
                className="absolute left-0 top-0 flex h-10 w-10 items-center justify-center text-ink-faint hover:text-ink"
              >
                <Search aria-hidden="true" size={18} strokeWidth={1.75} />
              </button>
              <label htmlFor="workspace-search" className="sr-only">
                Tìm trong tri thức dự án
              </label>
              <input
                id="workspace-search"
                name="q"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="h-10 w-full rounded-control border border-transparent bg-surface-quiet pl-10 pr-3 text-[14px] text-ink outline-none transition focus:border-brand focus:bg-surface focus:ring-2 focus:ring-brand-soft"
                placeholder="Tìm trong yêu cầu, kiểm thử hoặc lỗi"
              />
            </form>
          )}
          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                {projectId && (
                  <Link
                    href={`/qa/projects/${projectId}/knowledge`}
                    className="flex h-11 w-11 items-center justify-center rounded-control text-ink-muted hover:bg-surface-quiet hover:text-ink md:hidden"
                    aria-label="Tìm kiếm"
                  >
                    <Search size={19} strokeWidth={1.75} />
                  </Link>
                )}
                {notificationEnabled && (
                  <Link
                    href="/thong-bao"
                    className="relative flex h-11 w-11 items-center justify-center rounded-control text-ink-muted hover:bg-surface-quiet hover:text-ink"
                    aria-label={unreadCount ? `Thông báo, ${unreadCount} chưa đọc` : "Thông báo"}
                  >
                    <Bell size={19} strokeWidth={1.75} />
                    {unreadCount > 0 && (
                      <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-danger" />
                    )}
                  </Link>
                )}
                <div className="relative" ref={accountRef}>
                  <button
                    type="button"
                    onClick={() => setAccountOpen((value) => !value)}
                    className="flex h-10 items-center gap-2 rounded-control px-1.5 pr-2 text-left hover:bg-surface-quiet"
                    aria-expanded={accountOpen}
                  >
                    <span className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full bg-brand text-[13px] font-semibold text-white">
                      {user.avatar_url ? (
                        <Image
                          src={user.avatar_url}
                          alt=""
                          width={32}
                          height={32}
                          className="h-full w-full object-cover"
                          unoptimized
                        />
                      ) : (
                        initials
                      )}
                    </span>
                    <span className="hidden max-w-36 truncate text-[13px] font-semibold md:block">
                      {user.full_name || user.username}
                    </span>
                  </button>
                  {accountOpen && (
                    <div className="absolute right-0 top-12 w-60 rounded-panel border border-border bg-surface p-2 shadow-[0_18px_50px_rgba(48,47,42,0.12)]">
                      <div className="border-b border-border px-3 py-2.5">
                        <p className="truncate text-[14px] font-semibold text-ink">
                          {user.full_name || user.username}
                        </p>
                        <p className="truncate text-[12px] text-ink-muted">{user.email}</p>
                      </div>
                      <Link
                        href="/cai-dat"
                        className="mt-1 block rounded-control px-3 py-2 text-[14px] hover:bg-surface-quiet"
                      >
                        Cài đặt
                      </Link>
                      <button
                        type="button"
                        onClick={logoutState}
                        className="block w-full rounded-control px-3 py-2 text-left text-[14px] text-danger hover:bg-danger-soft"
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
                  className="flex min-h-11 items-center rounded-control px-3 py-2 text-[14px] font-semibold text-ink hover:bg-surface-quiet"
                >
                  Đăng nhập
                </Link>
                <Link
                  href="/dang-ky"
                  className="flex min-h-11 items-center rounded-control bg-brand px-4 py-2 text-[14px] font-semibold text-white hover:bg-brand-hover"
                >
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[260px] border-r border-border bg-surface lg:block">
        <div className="flex h-[68px] items-center border-b border-border px-5">
          <Link
            href="/"
            className="flex items-center gap-3 text-[19px] font-semibold tracking-[-0.035em] text-ink"
          >
            <Image
              src="/brand/veriq-logo.png"
              alt="Veriq"
              width={36}
              height={36}
              className="h-9 w-9 rounded-xl object-cover"
              priority
            />
            <span>Veriq</span>
          </Link>
        </div>
        <nav
          className="h-[calc(100dvh-68px)] overflow-y-auto px-4 py-6"
          aria-label="Điều hướng chính"
        >
          <NavigationList projectPermissions={projectPermissions} />
        </nav>
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-ink/30"
            onClick={() => setMobileOpen(false)}
            aria-label="Đóng điều hướng"
          />
          <aside className="relative h-full w-[min(88vw,320px)] overflow-y-auto bg-surface p-4 shadow-[20px_0_60px_rgba(32,32,30,0.16)]">
            <div className="mb-6 flex h-11 items-center justify-between">
              <Link
                href="/"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 text-[19px] font-semibold tracking-[-0.035em]"
              >
                <Image
                  src="/brand/veriq-logo.png"
                  alt="Veriq"
                  width={36}
                  height={36}
                  className="h-9 w-9 rounded-xl object-cover"
                />
                Veriq
              </Link>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="flex h-11 w-11 items-center justify-center rounded-control hover:bg-surface-quiet"
                aria-label="Đóng điều hướng"
              >
                <X size={20} strokeWidth={1.75} />
              </button>
            </div>
            <NavigationList
              onNavigate={() => setMobileOpen(false)}
              projectPermissions={projectPermissions}
            />
          </aside>
        </div>
      )}

      <main
        id="main-content"
        className="min-h-[100dvh] min-w-0 overflow-x-hidden pt-[68px] lg:pl-[260px]"
      >
        <div
          className={fullWidth ? "flex min-h-[calc(100dvh-68px)] w-full flex-col" : "page-shell"}
        >
          {children}
        </div>
      </main>
    </div>
  );
}
