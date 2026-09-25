import DataTable from "../../../components/DataTable";
import { Panel } from "../../../components/WorkspacePrimitives";
import { messageOf, valueLabel } from "../../../lib/testing";
import { testingApi } from "../../../services/testing.service";

export default function TestCaseTransferPanel({
  projectId,
  can,
  preview,
  setPreview,
  reload,
  onError,
}) {
  const exportCases = (format) => {
    testingApi.exportTestCases(projectId, format).catch((reason) => onError(messageOf(reason)));
  };
  const upload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      setPreview(await testingApi.uploadTestImport(projectId, file));
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const confirm = async () => {
    try {
      await testingApi.confirmTestImport(
        preview._id,
        preview.preview.map((_, index) => index),
      );
      setPreview(null);
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };

  return (
    <Panel
      title="Nhập và xuất ca kiểm thử"
      actions={
        <div className="flex flex-wrap gap-2">
          {can("testcase.export") && (
            <button className="secondary-button" type="button" onClick={() => exportCases("csv")}>
              Xuất CSV
            </button>
          )}
          {can("testcase.export") && (
            <button className="secondary-button" type="button" onClick={() => exportCases("xlsx")}>
              Xuất XLSX
            </button>
          )}
        </div>
      }
    >
      {can("testcase.import") && (
        <div className="space-y-4 p-5">
          <input
            className="apple-input"
            aria-label="Tệp ca kiểm thử CSV hoặc XLSX"
            type="file"
            accept=".csv,.xlsx"
            onChange={upload}
          />
          {preview && (
            <>
              <DataTable
                items={preview.preview.map((item, index) => ({ ...item, _id: index }))}
                empty="Tệp không có ca kiểm thử hợp lệ"
                columns={[
                  { key: "title", label: "Tên" },
                  { key: "type", label: "Loại", render: (item) => valueLabel(item.type) },
                  {
                    key: "priority",
                    label: "Ưu tiên",
                    render: (item) => valueLabel(item.priority),
                  },
                  { key: "expected", label: "Kết quả mong đợi" },
                ]}
              />
              <button className="apple-button" type="button" onClick={confirm}>
                Xác nhận nhập toàn bộ
              </button>
            </>
          )}
        </div>
      )}
    </Panel>
  );
}
