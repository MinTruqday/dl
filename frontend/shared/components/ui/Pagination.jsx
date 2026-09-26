export function Pagination({ value, page, pageSize, total, onChange }) {
  const pagination =
    value ||
    (Number.isFinite(page) && Number.isFinite(pageSize) && Number.isFinite(total)
      ? {
          page,
          total,
          total_pages: Math.ceil(total / pageSize),
        }
      : null);
  if (
    !pagination ||
    !Number.isFinite(pagination.page) ||
    !Number.isFinite(pagination.total) ||
    !Number.isFinite(pagination.total_pages) ||
    pagination.total_pages <= 1
  )
    return null;
  return (
    <nav
      aria-label="Phân trang"
      className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-4"
    >
      <p className="text-[12px] text-ink-muted">
        Trang {pagination.page} trên {pagination.total_pages} với {pagination.total} kết quả
      </p>
      <div className="flex gap-2">
        <button
          aria-label="Trang trước"
          className="secondary-button"
          disabled={pagination.page <= 1}
          type="button"
          onClick={() => onChange(pagination.page - 1)}
        >
          Trang trước
        </button>
        <button
          aria-label="Trang sau"
          className="secondary-button"
          disabled={pagination.page >= pagination.total_pages}
          type="button"
          onClick={() => onChange(pagination.page + 1)}
        >
          Trang sau
        </button>
      </div>
    </nav>
  );
}
