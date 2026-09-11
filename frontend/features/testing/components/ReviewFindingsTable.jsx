import DataTable from "./DataTable";
import { StatusPill } from "./WorkspacePrimitives";

export default function ReviewFindingsTable({ findings = [], canManage, onResolve }) {
  return (
    <DataTable
      items={findings}
      empty="Chưa có finding"
      columns={[
        { key: "severity", label: "Mức độ", render: (item) => <StatusPill value={item.severity} /> },
        { key: "category", label: "Nhóm" },
        { key: "description", label: "Nội dung" },
        { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
        { key: "action", label: "Thao tác", render: (item) => canManage && !["RESOLVED", "ACCEPTED"].includes(item.status) ? <button className="secondary-button" type="button" onClick={() => onResolve(item)}>Xử lý</button> : null },
      ]}
    />
  );
}
