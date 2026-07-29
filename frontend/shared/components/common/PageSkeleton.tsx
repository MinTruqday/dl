export default function PageSkeleton({
  cards = 4,
}: {
  cards?: number;
}) {
  return (
    <div className="app-page gap-6" aria-label="Đang tải dữ liệu" role="status">
      <div className="border-b border-[var(--border)] pb-6">
        <div className="h-8 w-44 rounded-[var(--radius-control)] bg-[var(--surface-quiet)]" />
        <div className="mt-3 h-4 w-full max-w-md rounded-[var(--radius-control)] bg-[var(--surface-quiet)]" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-hidden="true">
        {Array.from({ length: cards }, (_, index) => (
          <div
            key={index}
            className="h-28 rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)]"
          />
        ))}
      </div>
      <div
        className="h-72 rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)]"
        aria-hidden="true"
      />
    </div>
  );
}
