export default function PageLoader({ rows = 5, compact = false }) {
  return (
    <div
      className={`w-full ${compact ? "py-4" : "py-8"}`}
      role="status"
      aria-label="Đang tải dữ liệu"
    >
      <div className="mb-8 space-y-3">
        <div className="skeleton h-8 w-48" />
        <div className="skeleton h-4 w-full max-w-md" />
      </div>
      <div className="overflow-hidden rounded-panel border border-border bg-surface">
        <div className="grid min-h-11 grid-cols-[minmax(0,1fr)_7rem] items-center gap-4 border-b border-border px-4">
          <div className="skeleton h-3 w-28" />
          <div className="skeleton ml-auto h-3 w-16" />
        </div>
        <div className="divide-y divide-border">
          {Array.from({ length: rows }).map((_, index) => (
            <div
              key={index}
              className="grid min-h-16 grid-cols-[minmax(0,1fr)_7rem] items-center gap-4 px-4"
            >
              <div className="space-y-2">
                <div className="skeleton h-4 w-[min(72%,22rem)]" />
                <div className="skeleton h-3 w-[min(46%,14rem)]" />
              </div>
              <div className="skeleton ml-auto h-8 w-20" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
