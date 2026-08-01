type MetricItem = {
  label: string;
  value: string | number;
  detail?: string;
};

export default function MetricStrip({ items }: { items: MetricItem[] }) {
  return (
    <dl className="grid border-y border-border sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item, index) => (
        <div
          key={item.label}
          className={`min-w-0 py-4 sm:px-5 ${index ? "border-t border-border sm:border-l sm:border-t-0" : ""} ${index === 0 ? "sm:pl-0" : ""} ${index === 2 ? "sm:border-l-0 lg:border-l" : ""}`}
        >
          <dt className="text-[13px] font-medium text-ink-muted">
            {item.label}
          </dt>
          <dd className="mt-1 text-[22px] font-semibold tracking-[-0.02em] text-ink">
            {item.value}
          </dd>
          {item.detail && (
            <p className="mt-1 text-[12px] text-ink-faint">{item.detail}</p>
          )}
        </div>
      ))}
    </dl>
  );
}
