"use client";
import { EmptyState } from "./QaUi";

export default function DataTable({ columns, items, empty = "Chưa có dữ liệu", onSelect }) {
  if (!items?.length) return <EmptyState>{empty}</EmptyState>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-[13px]">
        <thead className="bg-surface-quiet text-[11px] uppercase tracking-wide text-ink-muted">
          <tr>
            {columns.map((column) => (
              <th className="px-4 py-3 font-semibold" key={column.key}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((item) => (
            <tr
              key={item._id || item.id}
              className={onSelect ? "cursor-pointer hover:bg-surface-quiet" : ""}
              onClick={() => onSelect?.(item)}
            >
              {columns.map((column) => (
                <td className="px-4 py-3 align-top" key={column.key}>
                  {column.render ? column.render(item) : String(item[column.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
