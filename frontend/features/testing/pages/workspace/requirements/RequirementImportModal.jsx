import DataTable from "../../../components/DataTable";
import { ErrorState } from "../../../components/WorkspacePrimitives";
import { docText, textDoc, valueLabel } from "../../../lib/testing";
import { Modal, ModalHeader, ModalTitle } from "@/shared/components/ui/Modal";
import { REQUIREMENT_IMPORT_FORMATS } from "./requirements.model";

export default function RequirementImportModal({
  isOpen,
  onClose,
  error,
  upload,
  setUpload,
  onUploadPreview,
  importValue,
  setImportValue,
  onImportPreview,
  preview,
  selectedIndexes,
  setSelectedIndexes,
  onSaveReview,
  onSplit,
  onMerge,
  onReject,
  onEditCandidate,
  onConfirm,
  sourceDocument,
  onRetrySource,
}) {
  const updateImportValue = (patch) => setImportValue((value) => ({ ...value, ...patch }));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      ariaLabel="Nhập tài liệu"
      className="max-w-5xl max-h-[90dvh] overflow-y-auto"
    >
      <ModalHeader>
        <ModalTitle>Nhập tài liệu</ModalTitle>
      </ModalHeader>
      {error && <ErrorState message={error} />}
      <form onSubmit={onUploadPreview} className="space-y-4 border-b border-border p-5">
        <label className="field-label">
          Tệp SRS BRD hoặc bảng yêu cầu
          <input
            className="apple-input mt-2"
            type="file"
            accept=".pdf,.docx,.txt,.md,.csv,.xlsx"
            onChange={(event) => setUpload(event.target.files?.[0] || null)}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={!upload}>
          Tải lên và xem trước
        </button>
      </form>
      <form onSubmit={onImportPreview} className="space-y-4 p-5">
        <label className="field-label">
          Tên tệp
          <input
            className="apple-input mt-2"
            value={importValue.filename}
            onChange={(event) => updateImportValue({ filename: event.target.value })}
          />
        </label>
        <label className="field-label">
          Định dạng
          <select
            className="apple-input mt-2"
            value={importValue.format}
            onChange={(event) => updateImportValue({ format: event.target.value })}
          >
            {REQUIREMENT_IMPORT_FORMATS.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Nội dung nguồn
          <textarea
            className="apple-input mt-2 min-h-48 font-mono"
            required
            value={importValue.content}
            onChange={(event) => updateImportValue({ content: event.target.value })}
          />
        </label>
        <button className="secondary-button" type="submit">
          Tạo bản xem trước
        </button>
      </form>
      {preview && (
        <div className="border-t border-border p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold">
                {preview.status === "CONFIRMED"
                  ? "Nguồn này đã được nhập trước đó"
                  : "Rà soát ứng viên trước khi nhập"}
              </p>
              <p className="mt-1 text-[12px] text-ink-muted">
                Đã chọn {selectedIndexes.length} trên {preview.preview.length} ứng viên
              </p>
            </div>
            {preview.status === "PREVIEW_READY" && (
              <div className="flex flex-wrap gap-2">
                <button className="secondary-button" type="button" onClick={onSaveReview}>
                  Lưu chỉnh sửa
                </button>
                <button className="secondary-button" type="button" onClick={onSplit}>
                  Tách mục đã chọn
                </button>
                <button className="secondary-button" type="button" onClick={onMerge}>
                  Gộp các mục đã chọn
                </button>
                <button className="danger-button" type="button" onClick={onReject}>
                  Từ chối mục đã chọn
                </button>
              </div>
            )}
          </div>
          <DataTable
            items={preview.preview.map((item, index) => ({
              ...item,
              _id: `candidate-${index}`,
              candidateIndex: index,
            }))}
            columns={[
              {
                key: "selected",
                label: "Nhập",
                render: (item) => (
                  <input
                    aria-label={`Chọn ứng viên ${item.candidateIndex + 1}`}
                    type="checkbox"
                    checked={selectedIndexes.includes(item.candidateIndex)}
                    disabled={preview.status !== "PREVIEW_READY"}
                    onChange={(event) =>
                      setSelectedIndexes((values) =>
                        event.target.checked
                          ? [...values, item.candidateIndex].sort((left, right) => left - right)
                          : values.filter((value) => value !== item.candidateIndex),
                      )
                    }
                  />
                ),
              },
              {
                key: "title",
                label: "Yêu cầu phát hiện",
                render: (item) => (
                  <input
                    aria-label={`Tên ứng viên ${item.candidateIndex + 1}`}
                    className="apple-input min-w-64"
                    value={item.title}
                    disabled={preview.status !== "PREVIEW_READY"}
                    onChange={(event) =>
                      onEditCandidate(item.candidateIndex, { title: event.target.value })
                    }
                  />
                ),
              },
              {
                key: "content_doc",
                label: "Nội dung",
                render: (item) => (
                  <textarea
                    aria-label={`Nội dung ứng viên ${item.candidateIndex + 1}`}
                    className="apple-input min-h-20 min-w-72"
                    value={docText(item.content_doc)}
                    disabled={preview.status !== "PREVIEW_READY"}
                    onChange={(event) =>
                      onEditCandidate(item.candidateIndex, {
                        content_doc: textDoc(event.target.value),
                      })
                    }
                  />
                ),
              },
              {
                key: "type",
                label: "Loại",
                render: (item) => valueLabel(item.type),
              },
              {
                key: "candidate_relation",
                label: "Quan hệ ứng viên",
                render: (item) => item.candidate_relation || "Nguyên bản",
              },
              {
                key: "extraction_confidence",
                label: "Độ tin cậy trích xuất",
                render: (item) => `${Math.round((item.extraction_confidence ?? 1) * 100)}%`,
              },
              {
                key: "source_refs",
                label: "Vị trí nguồn",
                render: (item) => {
                  const source = item.source_refs?.[0];
                  if (!source) return "Không có";
                  if (source.source_start !== undefined) {
                    return `${source.source_start} đến ${source.source_end}`;
                  }
                  return `Mục ${source.candidate_index + 1}`;
                },
              },
            ]}
          />
          {preview.status === "PREVIEW_READY" && (
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button
                className="apple-button"
                type="button"
                disabled={selectedIndexes.length === 0}
                onClick={onConfirm}
              >
                Xác nhận nhập {selectedIndexes.length} yêu cầu
              </button>
              <p className="text-[12px] text-ink-muted">
                {preview.preview.length - selectedIndexes.length} ứng viên bị loại sẽ không được ghi
              </p>
            </div>
          )}
        </div>
      )}
      {sourceDocument && (
        <div className="border-t border-border p-5 text-[12px] text-ink-muted">
          <p>Nguồn {sourceDocument.filename}</p>
          <p>Trạng thái {sourceDocument.status}</p>
          <p className="break-all">SHA256 {sourceDocument.content_hash}</p>
          {sourceDocument.status === "PARSE_FAILED" && (
            <button className="secondary-button mt-3" type="button" onClick={onRetrySource}>
              Thử phân tích lại từ tệp gốc
            </button>
          )}
        </div>
      )}
    </Modal>
  );
}
