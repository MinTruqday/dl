import ThresholdStatus from "./ThresholdStatus";

export default function QualityMetricCard({ definition, snapshot }) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{definition.name}</p>
          <p className="mt-1 text-xs text-ink-muted">{definition.objective}</p>
        </div>
        {snapshot && (
          <ThresholdStatus
            metricKey={definition.key}
            value={snapshot.value}
            target={definition.target}
            warning={definition.warning_threshold}
            critical={definition.critical_threshold}
          />
        )}
      </div>
      <p className="mt-4 text-2xl font-semibold">
        {snapshot ? `${snapshot.value} ${snapshot.unit}` : "Chưa đo"}
      </p>
      <p className="mt-2 text-xs text-ink-muted">{definition.formula}</p>
    </article>
  );
}
