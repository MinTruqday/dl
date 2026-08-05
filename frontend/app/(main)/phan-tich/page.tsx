"use client";

import Link from "next/link";
import {
  ArrowDown,
  ArrowUp,
  BarChart3,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Filter,
  Layers,
  Percent,
  RefreshCw,
  Search,
  ShoppingCart,
  TrendingUp,
  UserCheck,
  Users,
  Wallet,
  X,
} from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";
import EmptyState from "@/shared/components/common/EmptyState";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import { DocumentAnalyticsItem } from "@/features/management/services/analytics.service";
import { TimePreset, useAnalytics } from "./useAnalytics";

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
    search,
    setSearch,
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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-brand" />
            Phân tích số liệu và hiệu suất
          </h1>
          <p className="text-sm text-ink-muted mt-1">
            Trung tâm giám sát doanh thu lượt đọc tương tác độc giả và hoạt động toàn hệ thống
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1 bg-surface border border-border rounded-lg p-1 text-xs">
            <RefreshCw className={`h-3.5 w-3.5 text-ink-muted ${loading ? "animate-spin text-brand" : ""}`} />
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              aria-label="Tự động làm mới"
              className="bg-transparent text-ink text-xs focus:outline-none cursor-pointer"
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
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Tải lại
          </Button>

          <div className="relative inline-block text-left">
            <Button
              variant="secondary"
              size="sm"
              disabled={exporting}
              onClick={() => handleExport("csv")}
              className="flex items-center gap-1.5"
            >
              <FileSpreadsheet className="h-4 w-4 text-emerald-600" />
              Kết xuất CSV
            </Button>
          </div>

          <Button
            variant="secondary"
            size="sm"
            disabled={exporting}
            onClick={() => handleExport("json")}
            className="flex items-center gap-1.5"
          >
            <Download className="h-4 w-4 text-brand" />
            Kết xuất JSON
          </Button>
        </div>
      </div>

      {isAdmin && (
        <div className="flex border-b border-border gap-6">
          <button
            onClick={() => setTab("author")}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              tab === "author"
                ? "text-brand border-b-2 border-brand"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            Hiệu suất tác giả
          </button>
          <button
            onClick={() => setTab("system")}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              tab === "system"
                ? "text-brand border-b-2 border-brand"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            Báo cáo toàn hệ thống
          </button>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 bg-surface border border-border p-3.5 rounded-xl">
        <div className="flex flex-wrap items-center gap-2">
          <Calendar className="h-4 w-4 text-ink-muted mr-1" />
          <span className="text-xs font-medium text-ink-muted">Mốc thời gian:</span>
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
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                timePreset === key
                  ? "bg-brand text-white shadow-sm"
                  : "bg-surface-quiet text-ink hover:bg-surface-raised border border-border"
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
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Doanh thu</span>
                <Wallet className="h-4 w-4 text-emerald-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(overview.total_revenue)} dl
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Số dư: {number.format(overview.available_balance)} dl</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Lượt xem</span>
                <Eye className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(overview.total_views)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Từ tất cả tài liệu</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Lượt mua</span>
                <ShoppingCart className="h-4 w-4 text-purple-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(overview.total_purchases)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Giao dịch đã xác nhận</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Chuyển đổi</span>
                <Percent className="h-4 w-4 text-amber-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {overview.conversion_rate}%
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Tỷ lệ mua trên lượt xem</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Độc giả duy nhất</span>
                <UserCheck className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(overview.unique_buyers)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Người mua tài liệu</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Tài liệu xuất bản</span>
                <FileText className="h-4 w-4 text-teal-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(overview.total_documents)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Đang hoạt động</p>
            </div>
          </div>

          {trends.length > 0 && (
            <div className="p-5 rounded-xl border border-border bg-surface shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-ink flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-brand" />
                    Biến động doanh thu và giao dịch theo ngày
                  </h2>
                  <p className="text-xs text-ink-muted">Biểu đồ chuỗi thời gian ghi nhận các giao dịch mua tài liệu</p>
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
                <h2 className="text-base font-semibold text-ink flex items-center gap-2">
                  <Layers className="h-4 w-4 text-brand" />
                  Hiệu suất chi tiết từng tài liệu
                </h2>
                <p className="text-xs text-ink-muted">Danh sách số liệu tổng hợp của từng tác phẩm</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setPage(1);
                    }}
                    placeholder="Tìm kiếm tài liệu"
                    className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border bg-surface text-ink focus:outline-none focus:border-brand w-56"
                  />
                </div>

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
                description="Hãy xuất bản tài liệu đầu tiên để bắt đầu ghi nhận lượt đọc và doanh số"
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
                    <ChevronLeft className="h-4 w-4" />
                    Trước
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  >
                    Tiếp
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Doanh thu sàn</span>
                <Wallet className="h-4 w-4 text-emerald-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_revenue)} dl
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Toàn bộ nền tảng</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Lượt giao dịch</span>
                <ShoppingCart className="h-4 w-4 text-purple-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_purchases)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Lượt mua tài liệu</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Lượt xem toàn sàn</span>
                <Eye className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_views)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Tổng lưu lượng đọc</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Tài liệu xuất bản</span>
                <FileText className="h-4 w-4 text-teal-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_documents)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Tài liệu công khai</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Tổng người dùng</span>
                <Users className="h-4 w-4 text-indigo-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_users)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Tài khoản hệ thống</p>
            </div>

            <div className="p-4 rounded-xl border border-border bg-surface shadow-sm">
              <div className="flex items-center justify-between text-ink-muted mb-2">
                <span className="text-xs font-medium">Tổng tác giả</span>
                <UserCheck className="h-4 w-4 text-amber-600" />
              </div>
              <div className="text-xl font-bold text-ink tracking-tight">
                {number.format(systemData.total_authors)}
              </div>
              <p className="text-[11px] text-ink-muted mt-1">Tác giả sáng tạo</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-xl border border-border bg-surface shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-ink flex items-center gap-2">
                <Users className="h-4 w-4 text-brand" />
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
              <h2 className="text-base font-semibold text-ink flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand" />
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
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm transition-opacity">
          <div className="w-full max-w-md bg-surface border-l border-border h-full shadow-2xl p-6 overflow-y-auto space-y-6 animate-in slide-in-from-right">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <h3 className="text-lg font-bold text-ink flex items-center gap-2">
                <FileText className="h-5 w-5 text-brand" />
                Chi tiết hiệu suất tài liệu
              </h3>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1 rounded-lg text-ink-muted hover:text-ink hover:bg-surface-raised"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-ink-muted font-medium block">Tên tài liệu:</span>
                <span className="text-sm font-semibold text-ink mt-0.5 block">{selectedDoc.title}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 bg-surface-quiet p-3 rounded-lg border border-border">
                <div>
                  <span className="text-ink-muted block text-[11px]">Mã tài liệu</span>
                  <span className="font-mono text-ink text-[11px]">{selectedDoc.id}</span>
                </div>
                <div>
                  <span className="text-ink-muted block text-[11px]">Bảo vệ DRM</span>
                  <span className="font-semibold text-ink">
                    {selectedDoc.is_drm ? "Có kích hoạt" : "Không"}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted block text-[11px]">Giá niêm yết</span>
                  <span className="font-bold text-ink">
                    {selectedDoc.price > 0 ? `${number.format(selectedDoc.price)} dl` : "Miễn phí"}
                  </span>
                </div>
                <div>
                  <span className="text-ink-muted block text-[11px]">Tỷ trọng doanh thu</span>
                  <span className="font-bold text-brand">{selectedDoc.revenue_percentage}%</span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-ink text-xs uppercase tracking-wider">Chỉ số hoạt động</h4>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-lg border border-border bg-surface text-center">
                    <span className="text-[10px] text-ink-muted block">Lượt xem</span>
                    <span className="text-sm font-bold text-ink">{number.format(selectedDoc.views)}</span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface text-center">
                    <span className="text-[10px] text-ink-muted block">Lượt mua</span>
                    <span className="text-sm font-bold text-ink">{number.format(selectedDoc.purchases)}</span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface text-center">
                    <span className="text-[10px] text-ink-muted block">Chuyển đổi</span>
                    <span className="text-sm font-bold text-amber-600">{selectedDoc.conversion_rate}%</span>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
                <span className="text-[11px] text-emerald-800 font-medium block">Tổng doanh thu từ tác phẩm</span>
                <span className="text-xl font-bold text-emerald-600">
                  {number.format(selectedDoc.revenue)} dl
                </span>
              </div>

              {selectedDoc.last_purchased_at && (
                <div>
                  <span className="text-ink-muted font-medium block">Giao dịch mua gần nhất:</span>
                  <span className="text-ink font-mono mt-0.5 block">
                    {new Date(selectedDoc.last_purchased_at).toLocaleString("vi-VN")}
                  </span>
                </div>
              )}

              <div className="pt-4 border-t border-border flex items-center gap-2">
                <Link
                  href={`/tai-lieu/${selectedDoc.slug || selectedDoc.id}`}
                  className="flex-1 text-center py-2 px-3 rounded-lg bg-brand text-white font-medium hover:bg-brand-hover transition-colors"
                >
                  Xem trang tài liệu
                </Link>
                <Link
                  href={`/soan-thao/${selectedDoc.id}`}
                  className="py-2 px-3 rounded-lg border border-border bg-surface text-ink hover:bg-surface-raised font-medium transition-colors"
                >
                  Mở soạn thảo
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
