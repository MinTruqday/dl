import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import { API_URL } from "@/shared/services/api-client";

export type DocumentSummary = {
  _id?: string;
  id?: string;
  slug?: string;
  title?: string;
  description?: string;
  cover_url?: string;
  author?: { full_name?: string; username?: string };
  author_name?: string;
  categories?: string[];
  created_at?: string;
  views?: number;
  views_count?: number;
  average_rating?: number;
  price?: number;
  price_dl?: number;
  is_premium?: boolean;
};

type DocumentResultsProps = {
  documents: DocumentSummary[];
  loading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  compact?: boolean;
};

function coverUrl(value?: string) {
  if (!value) return "";
  if (value.startsWith("http") || value.startsWith("data:")) return value;
  return `${API_URL}/tai-len/luu-tru/${value}`;
}

function formatDate(value?: string) {
  if (!value) return "Gần đây";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Gần đây"
    : new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(date);
}

export default function DocumentResults({
  documents,
  loading = false,
  emptyTitle = "Chưa có tài liệu",
  emptyDescription,
  compact = false,
}: DocumentResultsProps) {
  if (loading) {
    return (
      <div
        className="overflow-hidden rounded-panel border border-border bg-surface"
        role="status"
        aria-label="Đang tải tài liệu"
      >
        {Array.from({ length: compact ? 3 : 6 }).map((_, index) => (
          <div
            key={index}
            className="flex min-h-24 gap-4 border-b border-border px-4 py-4 last:border-b-0"
          >
            <div className="skeleton h-16 w-12 shrink-0" />
            <div className="flex-1 space-y-3 py-1">
              <div className="skeleton h-4 w-2/3" />
              <div className="skeleton h-3 w-2/5" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!documents.length)
    return <EmptyState text={emptyTitle} description={emptyDescription} />;

  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      {documents.map((document, index) => {
        const id = document._id || document.id || String(index);
        const href = `/tai-lieu/${document.slug || id}`;
        const cover = coverUrl(document.cover_url);
        const author =
          document.author?.full_name ||
          document.author?.username ||
          document.author_name ||
          "Chưa rõ tác giả";
        const price = Number(document.price_dl ?? document.price ?? 0);
        return (
          <article
            key={id}
            className="border-b border-border last:border-b-0 hover:bg-surface-raised"
          >
            <Link
              href={href}
              className="grid min-h-24 gap-4 px-4 py-4 sm:grid-cols-[3.5rem_minmax(0,1fr)_10rem] sm:items-center"
            >
              <div className="hidden h-[72px] w-14 overflow-hidden rounded-control bg-surface-quiet sm:block">
                {cover ? (
                  <img
                    src={cover}
                    alt=""
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                ) : null}
              </div>
              <div className="min-w-0">
                <h3 className="truncate text-[15px] font-semibold text-ink">
                  {document.title || "Tài liệu chưa có tiêu đề"}
                </h3>
                <p className="mt-1 truncate text-[13px] text-ink-muted">
                  {author}
                </p>
                {!compact && document.description && (
                  <p className="mt-2 line-clamp-1 text-[13px] text-ink-muted">
                    {document.description}
                  </p>
                )}
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-faint sm:hidden">
                  <span>{formatDate(document.created_at)}</span>
                  <span>
                    {Number(
                      document.views_count ?? document.views ?? 0,
                    ).toLocaleString("vi-VN")}{" "}
                    lượt xem
                  </span>
                </div>
              </div>
              <div className="hidden text-right text-[12px] text-ink-muted sm:block">
                <p>{formatDate(document.created_at)}</p>
                <p className="mt-1">
                  {Number(
                    document.views_count ?? document.views ?? 0,
                  ).toLocaleString("vi-VN")}{" "}
                  lượt xem
                </p>
                <p className="mt-1 font-semibold text-ink">
                  {price > 0 || document.is_premium
                    ? `${price.toLocaleString("vi-VN")} dl`
                    : "Miễn phí"}
                </p>
              </div>
            </Link>
          </article>
        );
      })}
    </div>
  );
}
