import Link from "next/link";
import type { ExploreDocument, ExploreView } from "./types";

export default function DocumentCard({
  document,
  view,
}: {
  document: ExploreDocument;
  view: ExploreView;
}) {
  const author =
    document.author?.full_name || document.author?.username || "Ẩn danh";
  const date = document.created_at
    ? new Date(document.created_at).toLocaleDateString("vi-VN")
    : "Gần đây";

  return (
    <Link
      href={`/tai-lieu/${document.slug}`}
      className={`group overflow-hidden rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)] transition hover:border-[var(--border-strong)] ${
        view === "grid" ? "flex flex-col" : "flex items-center gap-5 p-4"
      }`}
    >
      <div
        className={`shrink-0 overflow-hidden bg-[var(--surface-quiet)] ${
          view === "grid"
            ? "aspect-[4/3] w-full"
            : "size-24 rounded-[var(--radius-control)]"
        }`}
      >
        {document.cover_url && (
          <img
            src={document.cover_url}
            alt=""
            className="size-full object-cover transition duration-300 group-hover:scale-[1.02]"
          />
        )}
      </div>
      <div className={view === "grid" ? "flex flex-1 flex-col p-5" : "min-w-0 flex-1"}>
        {document.categories?.[0] && (
          <p className="mb-2 text-[12px] font-medium text-[var(--brand)]">
            {document.categories[0]}
          </p>
        )}
        <h3 className="line-clamp-2 text-[17px] font-semibold leading-6 tracking-[-0.02em] text-[var(--ink)]">
          {document.title}
        </h3>
        <p className="mt-2 flex flex-wrap gap-x-3 text-[13px] text-[var(--ink-muted)]">
          <span className="truncate">{author}</span>
          <span>{date}</span>
        </p>
        <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 pt-4 text-[12px] text-[var(--ink-faint)]">
          <span>{document.views_count || 0} lượt xem</span>
          <span>{document.chapters_count || 0} chương</span>
        </div>
      </div>
    </Link>
  );
}
