import DataTable from "./DataTable";
import { valueLabel } from "../lib/testing";


function groups(values) {
  return (values || []).map((item, index) => ({ ...item, _id: item._id || `${item.type || "GROUP"}-${index}` }));
}


export default function TestwareHandoverPanel({ handover = [], archived = [], environments = [] }) {
  return (
    <section className="space-y-5">
      <div><h3 className="mb-3 font-semibold text-ink">Bàn giao testware</h3><DataTable items={groups(handover)} empty="Chưa có testware bàn giao" columns={[{ key: "type", label: "Loại", render: (item) => valueLabel(item.type) }, { key: "items", label: "Số lượng", render: (item) => Array.isArray(item.items) ? item.items.length : 1 }]} /></div>
      <div><h3 className="mb-3 font-semibold text-ink">Tài sản lưu trữ</h3><DataTable items={groups(archived)} empty="Không có tài sản lưu trữ" columns={[{ key: "type", label: "Loại", render: (item) => valueLabel(item.type) }, { key: "items", label: "Số lượng", render: (item) => Array.isArray(item.items) ? item.items.length : 1 }]} /></div>
      <div><h3 className="mb-3 font-semibold text-ink">Đóng môi trường</h3><DataTable items={groups(environments)} empty="Không có môi trường trong phạm vi" columns={[{ key: "name", label: "Môi trường", render: (item) => item.name || item.environment_id }, { key: "availability", label: "Khả dụng", render: (item) => valueLabel(item.availability || item.status) }, { key: "revision", label: "Revision" }]} /></div>
    </section>
  );
}
