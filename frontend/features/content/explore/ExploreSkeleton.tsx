export default function ExploreSkeleton() {
  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3" aria-hidden="true">
      {Array.from({ length: 6 }, (_, index) => (
        <div
          key={index}
          className="overflow-hidden rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)]"
        >
          <div className="aspect-[4/3] bg-[var(--surface-quiet)]" />
          <div className="space-y-3 p-5">
            <div className="h-3 w-20 rounded bg-[var(--surface-quiet)]" />
            <div className="h-5 w-full rounded bg-[var(--surface-quiet)]" />
            <div className="h-4 w-2/3 rounded bg-[var(--surface-quiet)]" />
          </div>
        </div>
      ))}
    </div>
  );
}
