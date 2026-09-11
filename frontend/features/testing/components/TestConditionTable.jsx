import DataTable from "./DataTable";
import { StatusPill } from "./WorkspacePrimitives";


export default function TestConditionTable({ items, onSelect }) {
  return <DataTable items={items} empty="Chưa có test condition" columns={[
    { key: "condition_key", label: "Mã" },
    { key: "title", label: "Condition" },
    { key: "coverage_item", label: "Coverage item" },
    { key: "risk", label: "Rủi ro", render: (item) => <StatusPill value={item.risk} /> },
    { key: "priority", label: "Ưu tiên", render: (item) => <StatusPill value={item.priority} /> },
    { key: "testability_status", label: "Testability", render: (item) => <StatusPill value={item.testability_status} /> },
    { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
    { key: "actions", label: "Thao tác", render: (item) => <button className="secondary-button" type="button" onClick={() => onSelect(item)}>Mở</button> },
  ]} />;
}
