import DataTable from "../../../components/DataTable";
import { Panel, StatusPill } from "../../../components/WorkspacePrimitives";
import { messageOf } from "../../../lib/testing";
import { testingApi } from "../../../services/testing.service";

export default function ApiArtifactsPanel({
  projectId,
  can,
  ask,
  apiImport,
  setApiImport,
  artifacts,
  operations,
  compareFrom,
  setCompareFrom,
  compareTo,
  setCompareTo,
  difference,
  setDifference,
  reload,
  onError,
}) {
  const confirmed = artifacts.filter((item) => item.status === "CONFIRMED");
  const importArtifact = async (event) => {
    event.preventDefault();
    try {
      await testingApi.importApiArtifact(projectId, apiImport);
      setApiImport((value) => ({ ...value, content: "" }));
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const review = async (item) => {
    try {
      await testingApi.reviewApiArtifact(item._id, {
        expected_revision: item.revision,
        selected_indexes: [],
        review_note: "Đã rà soát toàn bộ thao tác",
      });
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const confirm = async (item) => {
    try {
      await testingApi.confirmApiArtifact(item._id, {
        expected_revision: item.revision,
        idempotency_key: crypto.randomUUID(),
      });
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const archive = async (item) => {
    const answer = await ask({
      title: "Lưu trữ nguồn đặc tả API",
      description: item.filename,
      confirmLabel: "Lưu trữ",
      fields: [
        {
          name: "reason",
          label: "Lý do",
          initialValue: "Nguồn đặc tả không còn được sử dụng",
          required: true,
          multiline: true,
        },
      ],
    });
    if (!answer) return;
    try {
      await testingApi.archiveApiArtifact(item._id, {
        expected_revision: item.revision,
        reason: answer.reason,
      });
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const compare = async () => {
    try {
      setDifference(await testingApi.diffApiArtifacts(projectId, compareFrom, compareTo));
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const analyzeImpact = async () => {
    try {
      await testingApi.analyzeApiArtifactImpact(projectId, {
        from_artifact_id: compareFrom,
        to_artifact_id: compareTo,
      });
    } catch (reason) {
      onError(messageOf(reason));
    }
  };
  const generateTests = async (operation) => {
    try {
      await testingApi.generateApiTests(operation._id);
      await reload();
    } catch (reason) {
      onError(messageOf(reason));
    }
  };

  return (
    <Panel title="OpenAPI và Postman">
      <div className="grid gap-5 p-5 xl:grid-cols-2">
        {can("apiartifact.import") && (
          <form className="space-y-4" onSubmit={importArtifact}>
            <label className="field-label">
              Loại nguồn
              <select
                className="apple-input mt-2"
                value={apiImport.format}
                onChange={(event) =>
                  setApiImport((value) => ({
                    ...value,
                    format: event.target.value,
                    filename: `${event.target.value}.json`,
                  }))
                }
              >
                <option value="openapi">OpenAPI</option>
                <option value="postman">Postman</option>
              </select>
            </label>
            <label className="field-label">
              JSON đặc tả
              <textarea
                className="apple-input mt-2 min-h-48 font-mono"
                required
                value={apiImport.content}
                onChange={(event) =>
                  setApiImport((value) => ({ ...value, content: event.target.value }))
                }
              />
            </label>
            <button className="secondary-button" type="submit">
              Tạo bản xem trước
            </button>
          </form>
        )}
        <div className="space-y-5">
          <DataTable
            items={artifacts}
            empty="Chưa có nguồn đặc tả API"
            columns={[
              { key: "filename", label: "Nguồn" },
              { key: "format", label: "Định dạng" },
              {
                key: "status",
                label: "Trạng thái",
                render: (item) => <StatusPill value={item.status} />,
              },
              { key: "preview_count", label: "Thao tác" },
              {
                key: "actions",
                label: "Xử lý",
                render: (item) => (
                  <div className="flex flex-wrap gap-2">
                    {item.status === "PREVIEW_READY" && can("apiartifact.review") && (
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => review(item)}
                      >
                        Rà soát
                      </button>
                    )}
                    {item.status === "REVIEWED" && can("apiartifact.confirm") && (
                      <button className="apple-button" type="button" onClick={() => confirm(item)}>
                        Xác nhận
                      </button>
                    )}
                    {item.status !== "ARCHIVED" && can("apiartifact.archive") && (
                      <button className="danger-button" type="button" onClick={() => archive(item)}>
                        Lưu trữ
                      </button>
                    )}
                  </div>
                ),
              },
            ]}
          />
          {confirmed.length >= 2 && (
            <div className="rounded-2xl border border-[var(--border)] p-4">
              <div className="grid gap-3 md:grid-cols-2">
                <label className="field-label">
                  Phiên bản trước
                  <select
                    className="apple-input mt-2"
                    value={compareFrom}
                    onChange={(event) => setCompareFrom(event.target.value)}
                  >
                    {confirmed.map((item) => (
                      <option key={item._id} value={item._id}>
                        {item.filename}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field-label">
                  Phiên bản sau
                  <select
                    className="apple-input mt-2"
                    value={compareTo}
                    onChange={(event) => setCompareTo(event.target.value)}
                  >
                    {confirmed.map((item) => (
                      <option key={item._id} value={item._id}>
                        {item.filename}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className="secondary-button"
                  disabled={!compareFrom || !compareTo || compareFrom === compareTo}
                  type="button"
                  onClick={compare}
                >
                  So sánh đặc tả
                </button>
                {can("impact.execute") && (
                  <button
                    className="secondary-button"
                    disabled={!compareFrom || !compareTo || compareFrom === compareTo}
                    type="button"
                    onClick={analyzeImpact}
                  >
                    Phân tích ảnh hưởng
                  </button>
                )}
              </div>
              {difference && (
                <p className="mt-3 text-sm text-[var(--muted)]">
                  Thêm {difference.added.length} thay đổi {difference.changed.length} loại bỏ{" "}
                  {difference.removed.length}
                </p>
              )}
            </div>
          )}
          <DataTable
            items={operations}
            empty="Chưa có thao tác API đã xác nhận"
            columns={[
              { key: "method", label: "Phương thức" },
              { key: "path", label: "Đường dẫn" },
              { key: "title", label: "Tên" },
              {
                key: "generate",
                label: "Tạo ca kiểm thử",
                render: (item) =>
                  can("ai.generate_api_testcase") && can("testcase.create") ? (
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => generateTests(item)}
                    >
                      Tạo ca kiểm thử
                    </button>
                  ) : null,
              },
            ]}
          />
        </div>
      </div>
    </Panel>
  );
}
