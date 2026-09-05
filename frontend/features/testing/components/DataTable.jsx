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
  const toggleAll = () =>
    onSelectionChange(
      allSelected
        ? selectedIds.filter((id) => !pageIds.includes(id))
        : Array.from(new Set([...selectedIds, ...pageIds])),
    );
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
  const openFromKeyboard = (event, item) => {
    if (!onSelect || event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(item);
    }
  };
  return (
    <>
      <div className="hidden overflow-x-auto xl:block">
        <table
          className="w-full text-left text-[13px]"
          style={{ minWidth: `${Math.max(640, columns.length * 150 + (selectable ? 48 : 0))}px` }}
        >
          <thead className="bg-surface-quiet text-[11px] uppercase tracking-wide text-ink-muted">
            <tr>
              {selectable && (
                <th className="w-12 px-4 py-3">
                  <input
                    aria-label="Chọn tất cả mục trên trang"
                    checked={allSelected}
                    type="checkbox"
                    onChange={toggleAll}
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
                onKeyDown={(event) => openFromKeyboard(event, item)}
                tabIndex={onSelect ? 0 : undefined}
                aria-label={onSelect ? `Mở ${itemId(item) ?? `dòng ${index + 1}`}` : undefined}
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
                  <td className="min-w-0 break-words px-4 py-3 align-top" key={column.key}>
                    {renderValue(column, item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="space-y-3 p-4 xl:hidden">
        {selectable && (
          <label
            className="flex min-h-11 items-center gap-3 rounded-control border border-border bg-surface-raised px-3 text-[12px] font-semibold"
            onClick={(event) => event.stopPropagation()}
          >
            <input
              aria-label="Chọn tất cả mục trên trang"
              checked={allSelected}
              type="checkbox"
              onChange={toggleAll}
            />
            Chọn tất cả trên trang
          </label>
        )}
        {items.map((item, index) => (
          <article
            key={rowKey(item, index)}
            className={`rounded-xl border bg-surface-raised p-4 ${selectable && selectedIds.includes(itemId(item)) ? "border-brand" : "border-border"} ${onSelect ? "cursor-pointer active:border-brand" : ""}`}
            onClick={() => onSelect?.(item)}
            onKeyDown={(event) => openFromKeyboard(event, item)}
            tabIndex={onSelect ? 0 : undefined}
            aria-label={onSelect ? `Mở ${itemId(item) ?? `dòng ${index + 1}`}` : undefined}
          >
            {selectable && (
              <label
                className="mb-3 flex min-h-11 items-center gap-2 text-[12px] font-semibold"
                onClick={(event) => event.stopPropagation()}
              >
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
              {columns.map((column) => {
                const value = renderMobileValue(column, item);
                if (value === null || value === undefined || value === "") return null;
                return (
                  <div className="grid grid-cols-[minmax(0,40%)_1fr] gap-3" key={column.key}>
                    <dt className="text-[12px] font-semibold leading-5 text-ink-muted">
                      {column.label}
                    </dt>
                    <dd className="min-w-0 break-words text-[13px] text-ink">{value}</dd>
                  </div>
                );
              })}
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}
