import DataTable from "./DataTable";
import { StatusPill } from "./WorkspacePrimitives";

export default function PreventiveActionTable({ items = [], canManage, onAdvance }) {
  const next = { OPEN: "IN_PROGRESS", IN_PROGRESS: "IMPLEMENTED", IMPLEMENTED: "EFFECTIVENESS_REVIEW", EFFECTIVENESS_REVIEW: "CLOSED" };
  return <DataTable items={items} empty="Chưa có hành động CAPA" columns={[
    { key: "action_type", label: "Loại" }, { key: "title", label: "Hành động" }, { key: "owner_id", label: "Phụ trách" }, { key: "due_at", label: "Hạn" }, { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> }, { key: "action", label: "Thao tác", render: (item) => canManage && next[item.status] ? <button className="secondary-button" type="button" onClick={() => onAdvance(item, next[item.status])}>Chuyển {next[item.status]}</button> : null },
  ]} />;
}
