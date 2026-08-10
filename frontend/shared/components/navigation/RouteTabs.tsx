"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type RouteTab = {
  href: string;
  label: string;
  activePath?: string;
};

export default function RouteTabs({
  items,
  label,
}: {
  items: RouteTab[];
  label: string;
}) {
  const pathname = usePathname();

  return (
    <nav
      aria-label={label}
      className="mb-6 inline-flex max-w-full gap-1 overflow-x-auto rounded-control bg-surface-quiet p-1"
    >
      {items.map((item) => {
        const active = pathname === (item.activePath ?? item.href.split("?")[0]);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex min-h-11 items-center whitespace-nowrap rounded-control px-3 text-[13px] font-semibold transition duration-150 md:min-h-9 ${
              active
                ? "bg-surface text-ink shadow-[0_1px_3px_rgba(48,47,42,0.08)]"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
