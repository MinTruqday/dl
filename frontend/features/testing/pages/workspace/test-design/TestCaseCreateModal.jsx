import DocumentEditor from "../../../editor/DocumentEditor";
import { valueLabel } from "../../../lib/testing";
import { Modal, ModalHeader, ModalTitle } from "@/shared/components/ui/Modal";
import { selectedValues, TEST_CASE_TYPES, TEST_LEVELS } from "./testDesign.model";

export default function TestCaseCreateModal({
  isOpen,
  onClose,
  form,
  setForm,
  dataSets,
  testConditions,
  onSubmit,
}) {
  const update = (patch) => setForm((value) => ({ ...value, ...patch }));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      ariaLabel="Tạo ca kiểm thử"
      className="max-w-3xl max-h-[90dvh] overflow-y-auto"
    >
      <ModalHeader>
        <ModalTitle>Tạo ca kiểm thử</ModalTitle>
      </ModalHeader>
      <form onSubmit={onSubmit} className="space-y-4 p-5">
        <label className="field-label">
          Tên
          <input
            className="apple-input mt-2"
            required
            value={form.title}
            onChange={(event) => update({ title: event.target.value })}
          />
        </label>
        <div className="grid gap-3 sm:grid-cols-3">
          <select
            aria-label="Loại ca kiểm thử"
            className="apple-input"
            value={form.type}
            onChange={(event) => update({ type: event.target.value })}
          >
            {TEST_CASE_TYPES.map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
          <select
            aria-label="Ưu tiên ca kiểm thử"
            className="apple-input"
            value={form.priority}
            onChange={(event) => update({ priority: event.target.value })}
          >
            {TEST_LEVELS.map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
          <select
            aria-label="Rủi ro ca kiểm thử"
            className="apple-input"
            value={form.risk}
            onChange={(event) => update({ risk: event.target.value })}
          >
            {TEST_LEVELS.map((value) => (
              <option key={value} value={value}>
                {valueLabel(value)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <p className="field-label mb-2">Thao tác</p>
          <DocumentEditor
            value={form.action}
            onChange={(action) => update({ action })}
            label="Thao tác của ca kiểm thử"
            minHeight="min-h-24"
          />
        </div>
        <div>
          <p className="field-label mb-2">Kết quả mong đợi</p>
          <DocumentEditor
            value={form.expected}
            onChange={(expected) => update({ expected })}
            label="Kết quả mong đợi của ca kiểm thử"
            minHeight="min-h-24"
          />
        </div>
        <label className="field-label">
          Bộ dữ liệu tham số
          <select
            aria-label="Bộ dữ liệu cho ca kiểm thử mới"
            className="apple-input mt-2 min-h-28"
            multiple
            value={form.dataSetVersionIds}
            onChange={(event) => update({ dataSetVersionIds: selectedValues(event) })}
          >
            {dataSets.map((item) => (
              <option key={item.current_version_id} value={item.current_version_id}>
                {item.name} v{item.current_version?.version}
              </option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Điều kiện kiểm thử đã phê duyệt
          <select
            aria-label="Điều kiện kiểm thử cho ca kiểm thử mới"
            className="apple-input mt-2 min-h-28"
            multiple
            value={form.testConditionIds}
            onChange={(event) => update({ testConditionIds: selectedValues(event) })}
          >
            {testConditions.map((item) => (
              <option key={item._id} value={item._id}>
                {item.condition_key} {item.title}
              </option>
            ))}
          </select>
        </label>
        <div className="flex justify-end gap-3">
          <button className="secondary-button" type="button" onClick={onClose}>
            Hủy
          </button>
          <button className="apple-button" type="submit">
            Lưu bản nháp
          </button>
        </div>
      </form>
    </Modal>
  );
}
