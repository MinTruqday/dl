import test from "node:test";
import assert from "node:assert/strict";

import {
  docText,
  emptyDoc,
  messageOf,
  statusLabel,
  textDoc,
  valueLabel,
} from "../lib/qa.logic.mjs";

test("Tiptap documents retain plain text and preserve an empty document", () => {
  assert.deepEqual(emptyDoc(), { type: "doc", content: [] });
  assert.equal(docText(textDoc("Phone accepts 10 or 11 digits")), "Phone accepts 10 or 11 digits");
});

test("nested Tiptap content is projected in display order", () => {
  const document = {
    type: "doc",
    content: [
      { type: "heading", content: [{ type: "text", text: "Profile" }] },
      {
        type: "bulletList",
        content: [
          {
            type: "listItem",
            content: [{ type: "paragraph", content: [{ type: "text", text: "Phone validation" }] }],
          },
        ],
      },
    ],
  };
  assert.equal(docText(document), "Profile Phone validation");
});

test("QA status labels cover human review and version maintenance states", () => {
  assert.equal(statusLabel("SUGGESTED"), "AI đề xuất");
  assert.equal(statusLabel("NEEDS_UPDATE"), "Cần cập nhật");
  assert.equal(statusLabel("EDITED_ACCEPTED"), "Đã chấp nhận sau chỉnh sửa");
  assert.equal(statusLabel("BASELINED"), "Đã đặt làm phiên bản chuẩn");
  assert.equal(statusLabel("READY_FOR_RETEST"), "Sẵn sàng kiểm thử lại");
  assert.equal(statusLabel("DUPLICATE"), "Trùng lặp");
  assert.equal(statusLabel("SKIPPED"), "Đã bỏ qua");
  assert.equal(valueLabel("happy_path"), "Luồng thành công");
  assert.equal(valueLabel("critical"), "Nghiêm trọng");
});

test("service errors preserve actionable messages", () => {
  assert.equal(messageOf(new Error("REVISION_CONFLICT")), "REVISION_CONFLICT");
  assert.equal(messageOf(null), "Không thể hoàn tất thao tác");
});
