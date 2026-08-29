"use client";

import { useCallback, useEffect, useState } from "react";
import { docText, formatDate, messageOf, textDoc } from "../lib/testing";
import { testingApi } from "../services/testing.service";
import { ErrorState, Panel, StatusPill } from "./TestingUi";

export default function ReviewCommentsPanel({ projectId, artifactType, artifactId, title }) {
  const [items, setItems] = useState([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    if (!artifactId) return;
    try {
      const query = new URLSearchParams({
        artifact_type: artifactType,
        artifact_id: artifactId,
        status: "",
      });
      setItems(await testingApi.listReviewComments(projectId, query.toString()));
      setError("");
    } catch (reason) {
      setError(messageOf(reason));
    }
  }, [artifactId, artifactType, projectId]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async (event) => {
    event.preventDefault();
    const value = body.trim();
    if (!value) return;
    setSaving(true);
    try {
      await testingApi.createReviewComment(projectId, {
        artifact_type: artifactType,
        artifact_id: artifactId,
        body_doc: textDoc(value),
      });
      setBody("");
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setSaving(false);
    }
  };
  const transition = async (item) => {
    try {
      if (item.status === "OPEN") await testingApi.resolveReviewComment(item._id);
      else await testingApi.reopenReviewComment(item._id);
      await load();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };
  return (
    <Panel title={title || "Nhận xét rà soát"}>
      <div className="space-y-4 p-5">
        {error && <ErrorState message={error} />}
        {items.length ? (
          <ul className="divide-y divide-border rounded-xl border border-border">
            {items.map((item) => (
              <li className="space-y-3 p-4" key={item._id}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusPill value={item.status} />
                    <span className="text-[11px] text-ink-faint">{formatDate(item.created_at)}</span>
                  </div>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => transition(item)}
                  >
                    {item.status === "OPEN" ? "Đánh dấu đã xử lý" : "Mở lại"}
                  </button>
                </div>
                <p className="whitespace-pre-wrap text-[13px] leading-6">
                  {docText(item.body_doc) || "Nhận xét không có nội dung"}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[13px] text-ink-muted">Chưa có nhận xét rà soát</p>
        )}
        <form className="flex flex-col gap-3 sm:flex-row" onSubmit={create}>
          <textarea
            aria-label="Nội dung nhận xét"
            className="apple-input min-h-24 flex-1"
            required
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder="Nhập nhận xét có thể kiểm chứng"
          />
          <button className="apple-button self-end" type="submit" disabled={saving}>
            {saving ? "Đang lưu" : "Thêm nhận xét"}
          </button>
        </form>
      </div>
    </Panel>
  );
}
