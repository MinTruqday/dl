import { Panel, StatusPill } from "../../../components/WorkspacePrimitives";
import DocumentEditor from "../../../editor/DocumentEditor";
import { messageOf, valueLabel } from "../../../lib/testing";
import { testingApi } from "../../../services/testing.service";
import { REQUIREMENT_LEVELS, REQUIREMENT_TYPES } from "./requirements.model";

export default function RequirementCurrentVersionPanel({
  current,
  selected,
  draft,
  members,
  saveState,
  can,
  checkingWithAi,
  onCheckingChange,
  onLint,
  onError,
  saveDraft,
  onCreateVersion,
  onSplit,
  ask,
  reload,
  onReview,
  onDraftChange,
}) {
  return (
    <Panel
      title="Phiên bản hiện tại"
      actions={
        <div className="flex flex-wrap gap-2">
          {can("ai.run_lint") && (
            <button
              className="secondary-button"
              aria-busy={checkingWithAi}
              disabled={checkingWithAi}
              type="button"
              onClick={async () => {
                onCheckingChange(true);
                try {
                  const saved = await saveDraft();
                  const savedVersion = saved?.current_version || current;
                  onLint(
                    await testingApi.lintRequirement(savedVersion._id, {
                      idempotency_key: crypto.randomUUID(),
                      instruction: "Phân tích chất lượng và đề xuất bản sửa có căn cứ",
                    }),
                  );
                } catch (reason) {
                  onError(messageOf(reason));
                } finally {
                  onCheckingChange(false);
                }
              }}
            >
              {checkingWithAi ? "AI đang kiểm tra chất lượng" : "Kiểm tra chất lượng"}
            </button>
          )}
          {current.status === "BASELINED" && can("requirement.version.create") && (
            <button className="secondary-button" type="button" onClick={onCreateVersion}>
              Tạo phiên bản mới
            </button>
          )}
          {current.status === "BASELINED" && can("requirement.split") && (
            <button className="secondary-button" type="button" onClick={onSplit}>
              Tách yêu cầu
            </button>
          )}
          {current.status !== "OBSOLETE" && can("requirement.archive") && (
            <button
              className="secondary-button"
              type="button"
              onClick={async () => {
                const answer = await ask({
                  title: "Đánh dấu yêu cầu không còn hiệu lực",
                  description: `${selected.requirement_key} vẫn được giữ trong lịch sử truy vết`,
                  confirmLabel: "Đánh dấu",
                  danger: true,
                  fields: [
                    {
                      name: "reason",
                      label: "Lý do",
                      initialValue: "Yêu cầu không còn thuộc phạm vi sản phẩm",
                      required: true,
                      multiline: true,
                      autoFocus: true,
                    },
                  ],
                });
                if (!answer) return;
                try {
                  await testingApi.obsoleteRequirement(selected._id, {
                    expected_current_version_id: selected.current_version_id,
                    reason: answer.reason,
                  });
                  await reload();
                } catch (value) {
                  onError(messageOf(value));
                }
              }}
            >
              Đánh dấu không còn hiệu lực
            </button>
          )}
          {current.status === "OBSOLETE" && can("requirement.restore") && (
            <button
              className="secondary-button"
              type="button"
              onClick={async () => {
                const answer = await ask({
                  title: "Khôi phục yêu cầu",
                  description: `${selected.requirement_key} sẽ trở lại trạng thái trước khi bị đánh dấu không còn hiệu lực`,
                  confirmLabel: "Khôi phục",
                  fields: [
                    {
                      name: "reason",
                      label: "Lý do",
                      initialValue: "Yêu cầu tiếp tục thuộc phạm vi sản phẩm",
                      required: true,
                      multiline: true,
                      autoFocus: true,
                    },
                  ],
                });
                if (!answer) return;
                try {
                  await testingApi.restoreRequirement(selected._id, {
                    expected_current_version_id: selected.current_version_id,
                    reason: answer.reason,
                  });
                  await reload();
                } catch (value) {
                  onError(messageOf(value));
                }
              }}
            >
              Khôi phục yêu cầu
            </button>
          )}
          {current.status === "DRAFT" && can("requirement.submit_review") && (
            <button className="apple-button" type="button" onClick={() => onReview("submit")}>
              Gửi rà soát
            </button>
          )}
          {current.status === "IN_REVIEW" && can("requirement.onReview") && (
            <button className="secondary-button" type="button" onClick={() => onReview("changes")}>
              Yêu cầu chỉnh sửa
            </button>
          )}
          {current.status === "IN_REVIEW" && can("requirement.approve") && (
            <button className="apple-button" type="button" onClick={() => onReview("approve")}>
              Phê duyệt phiên bản
            </button>
          )}
        </div>
      }
    >
      <div className="grid gap-5 p-5 md:grid-cols-3">
        <div>
          <p className="field-label">Trạng thái</p>
          <div className="mt-2">
            <StatusPill value={current.status} />
          </div>
        </div>
        <div>
          <p className="field-label">Phiên bản</p>
          <p className="mt-2 font-semibold">v{current.version}</p>
        </div>
        <div>
          <p className="field-label">Rủi ro</p>
          <p className="mt-2 font-semibold">{current.risk}</p>
        </div>
        {current.status === "DRAFT" && draft && can("requirement.update") ? (
          <div className="space-y-4 md:col-span-3">
            <input
              aria-label="Tên yêu cầu"
              className="apple-input"
              value={draft.title}
              onChange={(event) => onDraftChange({ title: event.target.value })}
            />
            <div className="grid gap-3 sm:grid-cols-3">
              <select
                aria-label="Loại yêu cầu"
                className="apple-input"
                value={draft.type}
                onChange={(event) => onDraftChange({ type: event.target.value })}
              >
                {REQUIREMENT_TYPES.map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Ưu tiên yêu cầu"
                className="apple-input"
                value={draft.priority}
                onChange={(event) => onDraftChange({ priority: event.target.value })}
              >
                {REQUIREMENT_LEVELS.map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
              <select
                aria-label="Rủi ro yêu cầu"
                className="apple-input"
                value={draft.risk}
                onChange={(event) => onDraftChange({ risk: event.target.value })}
              >
                {REQUIREMENT_LEVELS.map((value) => (
                  <option key={value} value={value}>
                    {valueLabel(value)}
                  </option>
                ))}
              </select>
            </div>
            <DocumentEditor
              value={draft.content_doc}
              onChange={(content_doc) => onDraftChange({ content_doc })}
              label="Nội dung yêu cầu"
            />
            <textarea
              aria-label="Tiêu chí chấp nhận"
              className="apple-input min-h-28"
              value={draft.acceptance}
              onChange={(event) => onDraftChange({ acceptance: event.target.value })}
            />
            <div className="grid gap-3 lg:grid-cols-3">
              <textarea
                aria-label="Quy tắc nghiệp vụ"
                className="apple-input min-h-24"
                value={draft.businessRules}
                onChange={(event) => onDraftChange({ businessRules: event.target.value })}
                placeholder="Mỗi dòng một quy tắc nghiệp vụ"
              />
              <textarea
                aria-label="Tác nhân"
                className="apple-input min-h-24"
                value={draft.actors}
                onChange={(event) => onDraftChange({ actors: event.target.value })}
                placeholder="Các tác nhân phân tách bằng dấu phẩy"
              />
              <textarea
                aria-label="Phụ thuộc yêu cầu"
                className="apple-input min-h-24"
                value={draft.dependencies}
                onChange={(event) => onDraftChange({ dependencies: event.target.value })}
                placeholder="Mỗi dòng một phụ thuộc"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <input
                aria-label="Nhãn yêu cầu"
                className="apple-input"
                value={draft.tags}
                onChange={(event) => onDraftChange({ tags: event.target.value })}
                placeholder="Nhãn phân cách bằng dấu phẩy"
              />
              <select
                aria-label="Người phụ trách yêu cầu"
                className="apple-input"
                value={draft.ownerId}
                onChange={(event) => onDraftChange({ ownerId: event.target.value })}
              >
                <option value="">Chưa phân công</option>
                {members.map((item) => (
                  <option key={item.user_id} value={item.user_id}>
                    {item.user_label || item.user?.email || item.user_id}
                  </option>
                ))}
              </select>
            </div>
            <button className="secondary-button" type="button" onClick={saveDraft}>
              Lưu bản nháp
            </button>
            <span className="ml-3 text-[12px] text-ink-muted" aria-live="polite">
              {saveState === "saving"
                ? "Đang tự động lưu"
                : saveState === "pending"
                  ? "Có thay đổi chưa lưu"
                  : saveState === "error"
                    ? "Tự động lưu thất bại"
                    : "Đã tự động lưu"}
            </span>
          </div>
        ) : (
          <div className="md:col-span-3">
            <DocumentEditor
              value={current.content_doc}
              onChange={() => {}}
              label="Nội dung yêu cầu"
              readOnly
            />
          </div>
        )}
      </div>
    </Panel>
  );
}
