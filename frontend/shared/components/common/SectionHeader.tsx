export default function SectionHeader({
  title,
  action,
}: {
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-10 items-center justify-between gap-4">
      <h2 className="text-[16px] font-semibold tracking-[-0.015em] text-[var(--ink)]">
        {title}
      </h2>
      {action}
    </div>
  );
}
