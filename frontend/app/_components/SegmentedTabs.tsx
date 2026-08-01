type Tab<T extends string> = {
  id: T;
  label: string;
  count?: number;
};

type SegmentedTabsProps<T extends string> = {
  tabs: Tab<T>[];
  value: T;
  onChange: (value: T) => void;
  label: string;
};

export default function SegmentedTabs<T extends string>({
  tabs,
  value,
  onChange,
  label,
}: SegmentedTabsProps<T>) {
  return (
    <div
      className="inline-flex max-w-full gap-1 overflow-x-auto rounded-control bg-surface-quiet p-1"
      role="tablist"
      aria-label={label}
    >
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={value === tab.id}
          onClick={() => onChange(tab.id)}
          className={`min-h-9 whitespace-nowrap rounded-control px-3 text-[13px] font-semibold transition duration-150 ${value === tab.id ? "bg-surface text-ink shadow-[0_1px_3px_rgba(48,47,42,0.08)]" : "text-ink-muted hover:text-ink"}`}
        >
          {tab.label}
          {typeof tab.count === "number" ? ` ${tab.count}` : ""}
        </button>
      ))}
    </div>
  );
}
