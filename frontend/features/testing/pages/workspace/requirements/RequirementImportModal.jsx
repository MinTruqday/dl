import DataTable from "../../../components/DataTable";
import { ErrorState } from "../../../components/WorkspacePrimitives";
import DocumentEditor from "../../../editor/DocumentEditor";
import { docText, valueLabel } from "../../../lib/testing";
import { Modal, ModalHeader, ModalTitle } from "@/shared/components/ui/Modal";
import { REQUIREMENT_IMPORT_FORMATS } from "./requirements.model";

function DocumentAccessControl({ access, members, onChange, privateLabel, name }) {
  const isPublic = access.visibility !== "private";
  const updateSharedWith = (userId, checked) =>
    onChange({
      ...access,
      shared_with: checked
        ? [...access.shared_with, userId]
        : access.shared_with.filter((value) => value !== userId),
    });

  return (
    <fieldset className="space-y-3">
      <legend className="field-label">Quyền xem tài liệu</legend>
      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            checked={!isPublic}
            name={`${name}-visibility`}
            type="radio"
            onChange={() => onChange({ visibility: "private", shared_with: [] })}
          />
          {privateLabel}
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            checked={isPublic}
            name={`${name}-visibility`}
            type="radio"
            onChange={() =>
              onChange({
                visibility: access.visibility === "private" ? "project" : access.visibility,
                shared_with: access.shared_with,
              })
            }
          />
          Công khai
        </label>
      </div>
      {isPublic && (
        <fieldset className="space-y-2 rounded-control border border-border bg-surface-quiet p-3">
          <legend className="px-1 text-sm font-medium">Phạm vi công khai</legend>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={access.visibility === "project"}
              name={`${name}-scope`}
              type="radio"
              onChange={() => onChange({ visibility: "project", shared_with: [] })}
            />
            Tất cả thành viên dự án
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              checked={access.visibility === "shared"}
              name={`${name}-scope`}
              type="radio"
              onChange={() => onChange({ visibility: "shared", shared_with: access.shared_with })}
            />
            Cá nhân
          </label>
          {access.visibility === "shared" && (
            <div className="space-y-2 border-t border-border pt-3">
              <p className="text-sm font-medium">Chọn người được xem</p>
              {members.map((member) => (
                <label className="flex items-center gap-2 text-sm" key={member.user_id}>
                  <input
                    type="checkbox"
                    checked={access.shared_with.includes(member.user_id)}
                    onChange={(event) => updateSharedWith(member.user_id, event.target.checked)}
                  />
                  {member.user_label || member.user_id}
                </label>
              ))}
            </div>
          )}
        </fieldset>
      )}
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={Boolean(access.ai_enabled)}
          disabled={Boolean(access.ai_enabled)}
          onChange={(event) => onChange({ ...access, ai_enabled: event.target.checked })}
        />
        {access.ai_enabled
          ? "Đã cho phép AI truy cập tài liệu này"
          : "Cho phép AI truy cập tài liệu này"}
      </label>
    </fieldset>
  );
}

export default function RequirementImportModal({
  isOpen,
  onClose,
  error,
  upload,
  setUpload,
  uploadAccess,
  setUploadAccess,
  members,
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
        <DocumentAccessControl
          access={uploadAccess}
          members={members}
          name="upload-document"
          privateLabel="Riêng tư chỉ người tải lên"
          onChange={setUploadAccess}
        />
        <button
          className="secondary-button"
          type="submit"
          disabled={
            !upload || (uploadAccess.visibility === "shared" && !uploadAccess.shared_with.length)
          }
        >
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
        <DocumentAccessControl
          access={importValue}
          members={members}
          name="manual-document"
          privateLabel="Riêng tư chỉ người tạo"
          onChange={updateImportValue}
        />
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
          <div className="mt-2">
            <DocumentEditor
              label="nội dung nguồn"
              minHeight="min-h-64"
              value={importValue.content}
              onChange={(content) => updateImportValue({ content })}
            />
          </div>
        </label>
        <button
          className="secondary-button"
          type="submit"
          disabled={
            !docText(importValue.content) ||
            (importValue.visibility === "shared" && !importValue.shared_with.length)
          }
        >
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
              {preview.status === "PREVIEW_READY" && (
                <p className="mt-1 text-[12px] text-ink-muted">
                  Có thể biên tập đầy đủ nội dung đã trích xuất trước khi xác nhận nhập
                </p>
              )}
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
                  <div className="min-w-[36rem]">
                    <DocumentEditor
                      label={`nội dung ứng viên ${item.candidateIndex + 1}`}
                      minHeight="min-h-40"
                      readOnly={preview.status !== "PREVIEW_READY"}
                      value={item.content_doc}
                      onChange={(content_doc) =>
                        onEditCandidate(item.candidateIndex, { content_doc })
                      }
                    />
                  </div>
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
