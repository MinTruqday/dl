"use client";

import { useState } from "react";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import { useAdminReports } from "./useAdminReports";

type Filter = "pending" | "closed";

export default function ReportsPage() {
  const [filter, setFilter] = useState<Filter>("pending");
  const [query, setQuery] = useState("");
  const [confirmation, setConfirmation] = useState<{
    id: string;
    status: "RESOLVED" | "DISMISSED";
  } | null>(null);
  const {
    reports,
    total,
    allowed,
    loading,
    processing,
    error,
    reload,
    update,
  } = useAdminReports(query, filter);

  if (loading) return <PageLoader rows={6} />;
  if (!allowed)
    return (
      <InlineState
        title="Không có quyền truy cập"
        detail="Trang này chỉ dành cho quản trị viên"
        tone="danger"
      />
    );

  const confirm = async () => {
    if (!confirmation) return;
    if (await update(confirmation.id, confirmation.status))
      setConfirmation(null);
  };

  return (
    <div className="w-full">
      <PageHeader
        title="Báo cáo"
        meta={`${total} báo cáo`}
        actions={
          <Button variant="secondary" onClick={reload}>
            Làm mới
          </Button>
        }
      />
      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể cập nhật báo cáo"
            detail={error}
            tone="danger"
          />
        </div>
      )}
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <SegmentedTabs<Filter>
          label="Trạng thái báo cáo"
          value={filter}
          onChange={setFilter}
          tabs={[
            { id: "pending", label: "Chờ xử lý" },
            { id: "closed", label: "Đã đóng" },
          ]}
        />
        <div className="w-full sm:max-w-xs">
          <label
            htmlFor="report-search"
            className="mb-2 block text-[12px] font-semibold text-ink-muted"
          >
            Tìm báo cáo
          </label>
          <input
            id="report-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="apple-input w-full"
          />
        </div>
      </div>
      {!reports.length ? (
        <EmptyState
          text="Không có báo cáo trong nhóm này"
          description="Báo cáo phù hợp với trạng thái và từ khóa sẽ xuất hiện tại đây"
        />
      ) : (
        <div className="overflow-x-auto rounded-panel border border-border bg-surface">
          <table className="w-full min-w-[760px] border-collapse text-left">
            <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
              <tr>
                <th className="px-4 py-3">Nội dung</th>
                <th className="px-4 py-3">Đối tượng</th>
                <th className="px-4 py-3">Người gửi</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {reports.map((report) => {
                const id = report._id || report.id || "";
                const closed = ["RESOLVED", "DISMISSED"].includes(
                  String(report.status || "").toUpperCase(),
                );
                return (
                  <tr key={id} className="text-[13px] hover:bg-surface-raised">
                    <td className="max-w-sm px-4 py-3.5">
                      <p className="font-semibold text-ink">
                        {report.reason || "Chưa nêu lý do"}
                      </p>
                      <p className="mt-1 line-clamp-2 text-ink-muted">
                        {report.description || "Không có mô tả"}
                      </p>
                    </td>
                    <td className="px-4 py-3.5 text-ink-muted">
                      {report.target_type || report.item_type || "Nội dung"}
                      <p className="mt-1 max-w-40 truncate font-mono text-[11px]">
                        {report.target_id || report.item_id || "Không có"}
                      </p>
                    </td>
                    <td className="px-4 py-3.5 text-ink-muted">
                      {report.reporter_name || "Ẩn danh"}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-ink">
                      {closed
                        ? report.status === "RESOLVED"
                          ? "Đã xử lý"
                          : "Đã bỏ qua"
                        : "Chờ xử lý"}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      {!closed && (
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setConfirmation({ id, status: "DISMISSED" })
                            }
                          >
                            Bỏ qua
                          </Button>
                          <Button
                            size="sm"
                            onClick={() =>
                              setConfirmation({ id, status: "RESOLVED" })
                            }
                          >
                            Xử lý
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Modal
        isOpen={Boolean(confirmation)}
        onClose={() => !processing && setConfirmation(null)}
      >
        <ModalHeader>
          <ModalTitle>Xác nhận cập nhật</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            Trạng thái báo cáo sẽ được lưu vào nhật ký quản trị
          </p>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setConfirmation(null)}
            disabled={processing}
          >
            Hủy
          </Button>
          <Button onClick={confirm} disabled={processing}>
            {processing ? "Đang cập nhật" : "Xác nhận"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
