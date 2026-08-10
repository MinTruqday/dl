"use client";

import Link from "next/link";
import { ArrowDown, ArrowUp } from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";
import EmptyState from "@/shared/components/common/EmptyState";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import { DocumentAnalyticsItem } from "@/features/management/services/analytics.service";
import { TimePreset, useAnalytics } from "../hooks/useAnalytics";

const number = new Intl.NumberFormat("vi-VN");

export default function AnalyticsPage() {
  const {
    tab,
    setTab,
    isAdmin,
    timePreset,
    setTimePreset,
    customFromDate,
    setCustomFromDate,
    customToDate,
    setCustomToDate,
    overview,
    trends,
    documents,
    totalDocs,
    totalPages,
    page,
    setPage,
    pageSize,
    setPageSize,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    systemData,
    selectedDoc,
    setSelectedDoc,
    loading,
    error,
    exporting,
    autoRefreshInterval,
    setAutoRefreshInterval,
    lastRefreshedAt,
    reload,
    handleExport,
  } = useAnalytics();

  const maxTrendRevenue = Math.max(...trends.map((t) => t.revenue), 1);

  return (
    <div className="w-full space-y-6">
      <PageHeader
        title="Phân tích"
        actions={
          <>
          <div className="flex min-h-9 items-center rounded-control border border-border bg-surface px-2 text-[12px]">
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              aria-label="Tự động làm mới"
              className="cursor-pointer bg-transparent text-ink outline-none"
            >
              <option value={0}>Tự động làm mới: Tắt</option>
              <option value={5}>Làm mới: 5 giây</option>
              <option value={10}>Làm mới: 10 giây</option>
              <option value={30}>Làm mới: 30 giây</option>
            </select>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={reload}
            disabled={loading}
          >
            Tải lại
          </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={exporting}
              onClick={() => handleExport("csv")}
            >
              Xuất CSV
            </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={exporting}
            onClick={() => handleExport("json")}
          >
            Xuất JSON
          </Button>
          </>
        }
      />

      {isAdmin && (
        <SegmentedTabs
          label="Phạm vi phân tích"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "author", label: "Của tôi" },
            { id: "system", label: "Toàn hệ thống" },
          ]}
        />
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-ink-muted">Thời gian</span>
          {(
            [
              ["all", "Toàn bộ"],
              ["today", "Hôm nay"],
              ["7d", "7 ngày qua"],
              ["30d", "30 ngày qua"],
              ["90d", "90 ngày qua"],
              ["custom", "Tùy chỉnh"],
            ] as [TimePreset, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTimePreset(key)}
              className={`min-h-9 rounded-control px-3 text-xs font-medium transition ${
                timePreset === key
                  ? "bg-brand-soft text-brand"
                  : "text-ink-muted hover:bg-surface-quiet hover:text-ink"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {timePreset === "custom" && (
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={customFromDate}
              onChange={(e) => setCustomFromDate(e.target.value)}
              aria-label="Từ ngày"
              className="px-2.5 py-1 text-xs border border-border rounded bg-surface text-ink focus:outline-none focus:border-brand"
            />
            <span className="text-xs text-ink-muted">-</span>
            <input
              type="date"
              value={customToDate}
              onChange={(e) => setCustomToDate(e.target.value)}
              aria-label="Đến ngày"
              className="px-2.5 py-1 text-xs border border-border rounded bg-surface text-ink focus:outline-none focus:border-brand"
            />
          </div>
        )}
      </div>

      {error && (
        <InlineState
          title="Không thể tải số liệu phân tích"
          detail={error}
          tone="danger"
          action={
            <Button variant="secondary" onClick={reload}>
              Tải lại
            </Button>
          }
        />
      )}

      {loading && !overview.total_revenue && !systemData.total_revenue ? (
        <PageLoader rows={6} />
      ) : tab === "author" ? (
        <div className="space-y-6">
          <MetricStrip
            items={[
              { label: "Doanh thu", value: `${number.format(overview.total_revenue)} dl` },
              { label: "Số dư", value: `${number.format(overview.available_balance)} dl` },
              { label: "Lượt xem", value: number.format(overview.total_views) },
              { label: "Lượt mua", value: number.format(overview.total_purchases) },
              { label: "Chuyển đổi", value: `${overview.conversion_rate}%` },
              { label: "Tài liệu", value: number.format(overview.total_documents) },
            ]}
          />

          {trends.length > 0 && (
            <div className="p-5 rounded-xl border border-border bg-surface shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-ink">
                    Doanh thu theo ngày
                  </h2>
                </div>
              </div>

              <div className="h-48 flex items-end gap-1.5 pt-6 border-b border-border overflow-x-auto pb-2">
                {trends.map((item) => {
                  const heightPercent = Math.max(
                    Math.round((item.revenue / maxTrendRevenue) * 100),
                    item.revenue > 0 ? 8 : 2,
                  );
                  return (
                    <div
                      key={item.date}
                      className="flex-1 min-w-[28px] flex flex-col items-center gap-1 group relative cursor-pointer"
                    >
                      <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-ink text-white text-[10px] px-2 py-1 rounded shadow pointer-events-none whitespace-nowrap z-20">
                        <div>{item.date}</div>
                        <div>{number.format(item.revenue)} dl ({item.purchases} lượt)</div>
                      </div>

                      <div
                        style={{ height: `${heightPercent}%` }}
                        className={`w-full rounded-t transition-all ${
                          item.revenue > 0
                            ? "bg-brand hover:bg-brand-hover"
                            : "bg-surface-quiet border border-border"
                        }`}
                      />
                      <span className="text-[9px] text-ink-muted transform -rotate-45 origin-top-left mt-2 truncate w-8 block">
                        {item.date.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-ink">
                  Hiệu suất tài liệu
                </h2>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  aria-label="Sắp xếp theo tiêu chí"
                  className="px-2.5 py-1.5 text-xs rounded-lg border border-border bg-surface text-ink focus:outline-none cursor-pointer"
                >
                  <option value="revenue">Sắp xếp: Doanh thu</option>
                  <option value="views">Sắp xếp: Lượt xem</option>
                  <option value="purchases">Sắp xếp: Lượt mua</option>
                  <option value="conversion_rate">Sắp xếp: Chuyển đổi</option>
                  <option value="title">Sắp xếp: Tên A-Z</option>
                </select>

                <button
                  onClick={() => setSortOrder(sortOrder === "desc" ? "asc" : "desc")}
                  className="p-1.5 border border-border bg-surface rounded-lg text-ink hover:bg-surface-raised"
                  title="Đổi chiều sắp xếp"
                >
                  {sortOrder === "desc" ? <ArrowDown className="h-4 w-4" /> : <ArrowUp className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {documents.length === 0 ? (
              <EmptyState
                text="Chưa có dữ liệu phân tích tài liệu"
                actionLabel="Tạo bản thảo mới"
                actionHref="/soan-thao/khoi-tao"
              />
            ) : (
              <div className="overflow-x-auto rounded-xl border border-border bg-surface shadow-sm">
                <table className="w-full min-w-[760px] border-collapse text-left text-xs">
                  <thead className="bg-surface-quiet border-b border-border text-ink-muted uppercase font-semibold text-[11px]">
                    <tr>
                      <th className="px-4 py-3">Tài liệu</th>
                      <th className="px-4 py-3 text-right">Giá</th>
                      <th className="px-4 py-3 text-right">Lượt xem</th>
                      <th className="px-4 py-3 text-right">Lượt mua</th>
                      <th className="px-4 py-3 text-right">Tỷ lệ CR</th>
                      <th className="px-4 py-3 text-right">Doanh thu</th>
                      <th className="px-4 py-3">Tỷ trọng</th>
                      <th className="px-4 py-3 text-center">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-ink">
                    {documents.map((doc) => (
                      <tr
                        key={doc.id}
                        className="hover:bg-surface-raised transition-colors cursor-pointer"
                        onClick={() => setSelectedDoc(doc)}
                      >
                        <td className="px-4 py-3 max-w-xs">
                          <div className="font-semibold text-ink truncate hover:text-brand">
                            {doc.title}
                          </div>
                          <div className="text-[10px] text-ink-muted mt-0.5 flex items-center gap-1.5">
                            <span>Mã: {doc.id.slice(0, 8)}</span>
                            {doc.is_drm && (
                              <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-600 font-medium">
                                DRM
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-ink-muted">
                          {doc.price > 0 ? `${number.format(doc.price)} dl` : "Miễn phí"}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-ink-muted">
                          {number.format(doc.views)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums font-medium text-ink">
                          {number.format(doc.purchases)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-amber-600 font-semibold">
                          {doc.conversion_rate}%
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums font-bold text-emerald-600">
                          {number.format(doc.revenue)} dl
                        </td>
                        <td className="px-4 py-3 min-w-[120px]">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-surface-quiet border border-border rounded-full overflow-hidden">
                              <div
                                className="h-full bg-brand rounded-full"
                                style={{ width: `${Math.min(doc.revenue_percentage, 100)}%` }}
                              />
                            </div>
                            <span className="text-[10px] text-ink-muted tabular-nums w-8 text-right">
                              {doc.revenue_percentage}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setSelectedDoc(doc)}
                            className="px-2.5 py-1 text-xs rounded border border-border bg-surface-quiet hover:bg-surface-raised text-ink transition-colors"
                          >
                            Chi tiết
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-ink-muted">
                  Hiển thị trang {page} trên tổng số {totalPages} trang ({number.format(totalDocs)} tài liệu)
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  >
                    Trước
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  >
                    Tiếp
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <MetricStrip
            items={[
              { label: "Doanh thu", value: `${number.format(systemData.total_revenue)} dl` },
              { label: "Giao dịch", value: number.format(systemData.total_purchases) },
              { label: "Lượt xem", value: number.format(systemData.total_views) },
              { label: "Tài liệu", value: number.format(systemData.total_documents) },
              { label: "Người dùng", value: number.format(systemData.total_users) },
              { label: "Tác giả", value: number.format(systemData.total_authors) },
            ]}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-xl border border-border bg-surface shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-ink">
                Tác giả hàng đầu theo doanh thu
              </h2>
              {systemData.top_authors.length === 0 ? (
                <p className="text-xs text-ink-muted">Chưa có số liệu tác giả</p>
              ) : (
                <div className="divide-y divide-border">
                  {systemData.top_authors.map((author, index) => (
                    <div key={author.author_id} className="py-2.5 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-surface-quiet border border-border flex items-center justify-center font-bold text-[10px] text-ink-muted">
                          {index + 1}
                        </span>
                        <div>
                          <div className="font-semibold text-ink">{author.author_name}</div>
                          <div className="text-[10px] text-ink-muted">{author.purchases} lượt bán</div>
                        </div>
                      </div>
                      <div className="font-bold text-emerald-600 tabular-nums">
                        {number.format(author.revenue)} dl
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-5 rounded-xl border border-border bg-surface shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-ink">
                Tài liệu có doanh thu cao nhất
              </h2>
              {systemData.top_documents.length === 0 ? (
                <p className="text-xs text-ink-muted">Chưa có số liệu tài liệu</p>
              ) : (
                <div className="divide-y divide-border">
                  {systemData.top_documents.map((doc, index) => (
                    <div key={doc.document_id} className="py-2.5 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5 max-w-[70%]">
                        <span className="w-5 h-5 rounded-full bg-surface-quiet border border-border flex items-center justify-center font-bold text-[10px] text-ink-muted shrink-0">
                          {index + 1}
                        </span>
                        <div className="truncate">
                          <div className="font-semibold text-ink truncate">{doc.title}</div>
                          <div className="text-[10px] text-ink-muted">{doc.purchases} lượt mua</div>
                        </div>
                      </div>
                      <div className="font-bold text-emerald-600 tabular-nums">
                        {number.format(doc.revenue)} dl
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedDoc && (
        <Modal
          isOpen
          onClose={() => setSelectedDoc(null)}
          className="max-w-2xl"
        >
          <ModalHeader>
            <ModalTitle>Chi tiết hiệu suất tài liệu</ModalTitle>
          </ModalHeader>
          <ModalContent className="max-h-[70dvh] overflow-y-auto">
            <div>
              <p className="text-[12px] font-medium text-ink-muted">Tài liệu</p>
              <p className="mt-1 text-[15px] font-semibold text-ink">
                {selectedDoc.title}
              </p>
            </div>
            <dl className="grid gap-4 rounded-panel border border-border bg-surface-quiet p-4 sm:grid-cols-2">
              <div>
                <dt className="text-[12px] text-ink-muted">Mã tài liệu</dt>
                <dd className="mt-1 break-all font-mono text-[12px] text-ink">
                  {selectedDoc.id}
                </dd>
              </div>
              <div>
                <dt className="text-[12px] text-ink-muted">Bảo vệ DRM</dt>
                <dd className="mt-1 text-[13px] font-semibold text-ink">
                  {selectedDoc.is_drm ? "Đã bật" : "Chưa bật"}
                </dd>
              </div>
              <div>
                <dt className="text-[12px] text-ink-muted">Giá niêm yết</dt>
                <dd className="mt-1 text-[13px] font-semibold text-ink">
                  {selectedDoc.price > 0
                    ? `${number.format(selectedDoc.price)} dl`
                    : "Miễn phí"}
                </dd>
              </div>
              <div>
                <dt className="text-[12px] text-ink-muted">Tỷ trọng doanh thu</dt>
                <dd className="mt-1 text-[13px] font-semibold text-ink">
                  {selectedDoc.revenue_percentage}%
                </dd>
              </div>
            </dl>
            <MetricStrip
              items={[
                { label: "Lượt xem", value: number.format(selectedDoc.views) },
                { label: "Lượt mua", value: number.format(selectedDoc.purchases) },
                { label: "Chuyển đổi", value: `${selectedDoc.conversion_rate}%` },
                { label: "Doanh thu", value: `${number.format(selectedDoc.revenue)} dl` },
              ]}
            />
            {selectedDoc.last_purchased_at && (
              <p className="text-[13px] text-ink-muted">
                Giao dịch gần nhất: {new Date(selectedDoc.last_purchased_at).toLocaleString("vi-VN")}
              </p>
            )}
          </ModalContent>
          <ModalFooter>
            <Link
              href={`/soan-thao/chinh-sua?tai-lieu=${encodeURIComponent(selectedDoc.id)}`}
              className="secondary-button"
            >
              Mở soạn thảo
            </Link>
            <Link
              href={`/tai-lieu/${selectedDoc.slug || selectedDoc.id}`}
              className="pill-button"
            >
              Xem tài liệu
            </Link>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
}
