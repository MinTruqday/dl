"use client";
import { EmptyState } from "./QaUi";

export default function DataTable({ columns, items, empty = "Chưa có dữ liệu", onSelect }) {
  if (!items?.length) return <EmptyState>{empty}</EmptyState>;
  const renderValue = (column, item) =>
    column.render ? column.render(item) : String(item[column.key] ?? "");
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-[13px]">
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
                    {renderValue(column, item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="space-y-3 p-4 md:hidden">
        {items.map((item) => (
          <article
            key={item._id || item.id}
            className={`rounded-xl border border-border bg-surface-raised p-4 ${onSelect ? "cursor-pointer active:border-brand" : ""}`}
            onClick={() => onSelect?.(item)}
          >
            <dl className="space-y-3">
              {columns.map((column) => (
                <div className="grid grid-cols-[minmax(0,40%)_1fr] gap-3" key={column.key}>
                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                    {column.label}
                  </dt>
                  <dd className="min-w-0 break-words text-[13px] text-ink">
                    {renderValue(column, item)}
                  </dd>
                </div>
              ))}
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}
