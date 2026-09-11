import DataTable from "./DataTable";
import { StatusPill } from "./WorkspacePrimitives";


export default function TestControlActionPanel({ items, canCreate, canUpdate, onCreate, onUpdate }) {
  return (
    <div className="space-y-4">
      {canCreate && <div className="flex justify-end px-5 pt-5"><button className="apple-button" type="button" onClick={onCreate}>Tạo control action</button></div>}
      <DataTable items={items} empty="Chưa có control action" columns={[
        { key: "type", label: "Loại" },
        { key: "title", label: "Nội dung" },
        { key: "owner_id", label: "Người phụ trách" },
        { key: "due_at", label: "Hạn", render: (item) => new Date(item.due_at).toLocaleString("vi-VN") },
        { key: "priority", label: "Ưu tiên", render: (item) => <StatusPill value={item.priority} /> },
        { key: "status", label: "Trạng thái", render: (item) => <StatusPill value={item.status} /> },
        ...(canUpdate ? [{ key: "actions", label: "Thao tác", render: (item) => item.status === "OPEN" ? <button className="secondary-button" type="button" onClick={() => onUpdate(item, "IN_PROGRESS")}>Bắt đầu</button> : item.status === "IN_PROGRESS" ? <button className="secondary-button" type="button" onClick={() => onUpdate(item, "DONE")}>Hoàn tất</button> : null }] : []),
      ]} />
    </div>
  );
}
