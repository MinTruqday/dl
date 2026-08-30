"use client";
import { EmptyState } from "./TestingUi";

export default function DataTable({
  columns,
  items,
  empty = "Chưa có dữ liệu",
  onSelect,
  selectedIds,
  onSelectionChange,
  selectionLabel = "Chọn mục",
  getRowKey,
}) {
  if (!items?.length) return <EmptyState>{empty}</EmptyState>;
  const selectable = Array.isArray(selectedIds) && typeof onSelectionChange === "function";
  const itemId = (item) => item._id ?? item.id ?? item.key ?? item.code;
  const rowKey = (item, index) =>
    `${String(getRowKey?.(item, index) ?? itemId(item) ?? "dòng")}-${index}`;
  const pageIds = items.map(itemId).filter((id) => id !== undefined && id !== null);
  const allSelected =
    selectable && pageIds.length > 0 && pageIds.every((id) => selectedIds.includes(id));
  const toggle = (id) => {
    if (id === undefined || id === null) return;
    onSelectionChange(
      selectedIds.includes(id) ? selectedIds.filter((value) => value !== id) : [...selectedIds, id],
    );
  };
  const renderValue = (column, item) =>
    column.render ? column.render(item) : String(item[column.key] ?? "");
  const renderMobileValue = (column, item) =>
    column.mobileRender ? column.mobileRender(item) : renderValue(column, item);
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-[13px]">
          <thead className="bg-surface-quiet text-[11px] uppercase tracking-wide text-ink-muted">
            <tr>
              {selectable && (
                <th className="w-12 px-4 py-3">
                  <input
                    aria-label="Chọn tất cả mục trên trang"
                    checked={allSelected}
                    type="checkbox"
                    onChange={() =>
                      onSelectionChange(
                        allSelected
                          ? selectedIds.filter((id) => !pageIds.includes(id))
                          : Array.from(new Set([...selectedIds, ...pageIds])),
                      )
                    }
                  />
                </th>
              )}
              {columns.map((column) => (
                <th className="px-4 py-3 font-semibold" key={column.key}>
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {items.map((item, index) => (
              <tr
                key={rowKey(item, index)}
                className={onSelect ? "cursor-pointer hover:bg-surface-quiet" : ""}
                onClick={() => onSelect?.(item)}
              >
                {selectable && (
                  <td className="w-12 px-4 py-3 align-top">
                    <input
                      aria-label={`${selectionLabel} ${itemId(item)}`}
                      checked={selectedIds.includes(itemId(item))}
                      disabled={itemId(item) === undefined || itemId(item) === null}
                      type="checkbox"
                      onClick={(event) => event.stopPropagation()}
                      onChange={() => toggle(itemId(item))}
                    />
                  </td>
                )}
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
        {items.map((item, index) => (
          <article
            key={rowKey(item, index)}
            className={`rounded-xl border border-border bg-surface-raised p-4 ${onSelect ? "cursor-pointer active:border-brand" : ""}`}
            onClick={() => onSelect?.(item)}
          >
            {selectable && (
              <label className="mb-3 flex items-center gap-2 text-[12px] font-semibold">
                <input
                  aria-label={`${selectionLabel} ${itemId(item)}`}
                  checked={selectedIds.includes(itemId(item))}
                  disabled={itemId(item) === undefined || itemId(item) === null}
                  type="checkbox"
                  onClick={(event) => event.stopPropagation()}
                  onChange={() => toggle(itemId(item))}
                />
                Chọn
              </label>
            )}
            <dl className="space-y-3">
              {columns.map((column) => (
                <div className="grid grid-cols-[minmax(0,40%)_1fr] gap-3" key={column.key}>
                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-ink-faint">
                    {column.label}
                  </dt>
                  <dd className="min-w-0 break-words text-[13px] text-ink">
                    {renderMobileValue(column, item)}
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
