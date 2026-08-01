"use client";

import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { useVersionHistory } from "./useVersionHistory";
import DocumentWorkspaceNavigation from "../_components/DocumentWorkspaceNavigation";

function versionId(version: any) {
  return String(version._id ?? version.id ?? "");
}

export default function HistoryPage() {
  const state = useVersionHistory();
  if (state.loading && !state.documents.length) return <PageLoader rows={5} />;
  return (
    <div className="w-full">
      <DocumentWorkspaceNavigation />
      <PageHeader
        title="Lịch sử phiên bản"
        actions={
          <Button
            disabled={state.selected.length !== 2 || state.processing}
            onClick={state.compare}
          >
            So sánh bản đã chọn
          </Button>
        }
        meta={
          <label className="flex items-center gap-3">
            <span className="font-semibold text-ink">Tài liệu</span>
            <select
              value={state.documentId}
              onChange={(event) => state.setDocumentId(event.target.value)}
              className="apple-input min-w-64"
            >
              <option value="">Chọn tài liệu</option>
              {state.documents.map((document) => (
                <option
                  key={document._id ?? document.id}
                  value={document._id ?? document.id}
                >
                  {document.title || "Chưa đặt tên"}
                </option>
              ))}
            </select>
          </label>
        }
      />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể xử lý phiên bản"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {state.notice && (
        <div className="mb-6">
          <InlineState
            title={state.notice}
            action={
              <Button variant="ghost" onClick={state.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}
      {!state.documentId ? (
        <InlineState
          title="Chưa có tài liệu"
          detail="Tạo tài liệu để bắt đầu lưu phiên bản"
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-[17px] font-semibold text-ink">
                Các phiên bản
              </h2>
              <span className="text-[12px] text-ink-muted">
                Chọn tối đa hai bản
              </span>
            </div>
            {state.loading ? (
              <PageLoader rows={4} />
            ) : state.versions.length ? (
              <ul className="overflow-hidden rounded-panel border border-border bg-surface">
                {state.versions.map((version: any, index: number) => {
                  const id = versionId(version);
                  const checked = state.selected.includes(id);
                  return (
                    <li
                      key={id}
                      className="border-b border-border p-4 last:border-b-0"
                    >
                      <div className="flex items-start gap-3">
                        <input
                          aria-label={`Chọn phiên bản ${index + 1}`}
                          type="checkbox"
                          className="mt-1 h-4 w-4 accent-[hsl(var(--brand))]"
                          checked={checked}
                          onChange={() => state.toggle(id)}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-[14px] font-semibold text-ink">
                            {version.version_note ||
                              `Phiên bản ${version.version_number ?? index + 1}`}
                          </p>
                          <p className="mt-1 text-[12px] text-ink-muted">
                            {new Date(version.created_at).toLocaleString(
                              "vi-VN",
                            )}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={state.processing}
                          onClick={() => state.restore(id)}
                        >
                          Khôi phục
                        </Button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <InlineState
                title="Chưa có phiên bản"
                detail="Các bản lưu sẽ xuất hiện tại đây"
              />
            )}
          </section>
          <section>
            <h2 className="mb-3 text-[17px] font-semibold text-ink">
              Đối chiếu
            </h2>
            {state.comparison ? (
              <pre className="max-h-[640px] overflow-auto whitespace-pre-wrap rounded-panel border border-border bg-surface p-5 font-mono text-[12px] leading-relaxed text-ink">
                {typeof state.comparison === "string"
                  ? state.comparison
                  : JSON.stringify(state.comparison, null, 2)}
              </pre>
            ) : (
              <InlineState
                title="Chưa có kết quả đối chiếu"
                detail="Chọn hai phiên bản rồi thực hiện so sánh"
              />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
