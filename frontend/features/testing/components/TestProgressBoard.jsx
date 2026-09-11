import { Metric } from "./WorkspacePrimitives";


export default function TestProgressBoard({ metrics = {} }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <Metric label="Tiến độ thực thi" value={`${metrics.execution_percent || 0}%`} detail={`${metrics.executed_test_count || 0} trên ${metrics.planned_test_count || 0}`} />
      <Metric label="Tỷ lệ đạt" value={`${metrics.pass_rate || 0}%`} detail={`${metrics.pass || 0} đạt ${metrics.fail || 0} không đạt`} />
      <Metric label="Requirement coverage" value={`${metrics.requirement_coverage || 0}%`} />
      <Metric label="Test condition coverage" value={`${metrics.test_condition_coverage || 0}%`} />
      <Metric label="Lỗi blocker đang mở" value={metrics.open_blocker || 0} detail={`${metrics.open_critical || 0} lỗi critical`} />
    </div>
  );
}
