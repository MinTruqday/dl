export default function MetricStrip({ items }) {
  const columns =
    items.length === 2
      ? "sm:grid-cols-2"
      : items.length === 3
        ? "sm:grid-cols-3"
        : items.length === 4
          ? "sm:grid-cols-2 lg:grid-cols-4"
          : items.length === 5
            ? "sm:grid-cols-2 lg:grid-cols-5"
            : items.length === 6
              ? "sm:grid-cols-3 lg:grid-cols-6"
              : "sm:grid-cols-2 lg:grid-cols-4";
  const smColumns = items.length === 2 || items.length === 4 || items.length === 5 ? 2 : 3;
  const lgColumns = items.length > 3 && items.length <= 6 ? items.length : smColumns;
  const dividers = (index) => {
    if (!index) return "";
    return [
      "border-t border-border",
      index >= smColumns ? "sm:border-t" : "sm:border-t-0",
      index % smColumns ? "sm:border-l" : "sm:border-l-0",
      index >= lgColumns ? "lg:border-t" : "lg:border-t-0",
      index % lgColumns ? "lg:border-l" : "lg:border-l-0",
    ].join(" ");
  };
  return (
    <dl className={`grid border-y border-border ${columns}`}>
      {items.map((item, index) => (
        <div
          key={item.label}
          className={`min-w-0 py-4 sm:px-5 ${dividers(index)} ${index % smColumns === 0 ? "sm:pl-0" : ""} ${index % lgColumns === 0 ? "lg:pl-0" : ""} ${index % smColumns === smColumns - 1 ? "sm:pr-0" : ""} ${index % lgColumns === lgColumns - 1 ? "lg:pr-0" : ""}`}
        >
          <dt className="text-[13px] font-medium text-ink-muted">{item.label}</dt>
          <dd className="mt-1 text-[22px] font-semibold tracking-[-0.02em] text-ink">
            {item.value}
          </dd>
          {item.detail && <p className="mt-1 text-[12px] text-ink-faint">{item.detail}</p>}
        </div>
      ))}
    </dl>
  );
}
