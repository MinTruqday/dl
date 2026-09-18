export default function StatisticalControlChart({ analysis }) {
  const points = analysis?.points || [];
  const values = points.map((item) => Number(item.value));
  const limits = [
    Number(analysis?.lower_control_limit),
    Number(analysis?.center_line),
    Number(analysis?.upper_control_limit),
  ];
  const minimum = Math.min(...values, ...limits);
  const maximum = Math.max(...values, ...limits);
  const span = Math.max(maximum - minimum, 1);
  const x = (index) => (points.length === 1 ? 50 : 6 + (index * 88) / (points.length - 1));
  const y = (value) => 92 - ((Number(value) - minimum) * 84) / span;
  const path = points.map((item, index) => `${x(index)},${y(item.value)}`).join(" ");
  return (
    <div className="rounded-xl border border-border p-4">
      <svg
        aria-label={`Biểu đồ kiểm soát ${analysis?.baseline_label || ""}`}
        className="h-56 w-full"
        preserveAspectRatio="none"
        role="img"
        viewBox="0 0 100 100"
      >
        <line
          className="stroke-rose-500"
          strokeDasharray="2 2"
          x1="4"
          x2="96"
          y1={y(limits[2])}
          y2={y(limits[2])}
        />
        <line
          className="stroke-slate-500"
          strokeDasharray="2 2"
          x1="4"
          x2="96"
          y1={y(limits[1])}
          y2={y(limits[1])}
        />
        <line
          className="stroke-rose-500"
          strokeDasharray="2 2"
          x1="4"
          x2="96"
          y1={y(limits[0])}
          y2={y(limits[0])}
        />
        <polyline className="fill-none stroke-accent" points={path} strokeWidth="1.2" />
        {points.map((item, index) => (
          <circle
            className={item.outlier ? "fill-rose-600" : "fill-accent"}
            cx={x(index)}
            cy={y(item.value)}
            key={item.snapshot_id}
            r={item.outlier ? 2 : 1.4}
          >
            <title>{`${item.snapshot_id} ${item.value}`}</title>
          </circle>
        ))}
      </svg>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-ink-muted">
        <span>Giới hạn trên {analysis?.upper_control_limit}</span>
        <span>Đường trung tâm {analysis?.center_line}</span>
        <span>Giới hạn dưới {analysis?.lower_control_limit}</span>
      </div>
    </div>
  );
}
