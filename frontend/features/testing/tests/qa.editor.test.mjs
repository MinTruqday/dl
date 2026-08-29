import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const editorSource = await readFile(
  new URL("../editor/QaDocumentEditor.jsx", import.meta.url),
  "utf8",
);
const extensionSource = await readFile(new URL("../editor/extensions.js", import.meta.url), "utf8");

test("QA editor registers every Tiptap capability required by the V1 specification", () => {
  const packages = [
    "character-count",
    "code-block-lowlight",
    "color",
    "details",
    "details-content",
    "details-summary",
    "drag-handle",
    "emoji",
    "file-handler",
    "focus",
    "font-family",
    "highlight",
    "image",
    "invisible-characters",
    "list-keymap",
    "link",
    "mathematics",
    "mention",
    "placeholder",
    "subscript",
    "superscript",
    "table",
    "table-cell",
    "table-of-contents",
    "table-header",
    "table-row",
    "task-item",
    "task-list",
    "text-align",
    "text-style",
    "typography",
    "underline",
    "unique-id",
    "youtube",
  ];

  for (const name of packages) {
    assert.match(extensionSource, new RegExp(`@tiptap/extension-${name}`));
  }
  assert.match(extensionSource, /StarterKit\.configure\(\{ codeBlock: false \}\)/);
  assert.match(extensionSource, /CodeBlockLowlight\.configure\(\{ lowlight \}\)/);
  assert.match(extensionSource, /openOnClick: !editable/);
  assert.match(extensionSource, /Table\.configure\(\{ resizable: editable \}\)/);
  assert.match(extensionSource, /TableOfContents\.configure/);
  assert.match(editorSource, /BubbleMenu/);
  assert.match(editorSource, /FloatingMenu/);
});

test("QA editor exposes editing controls and preserves read only rendering", () => {
  for (const label of [
    "Đánh dấu",
    "Chỉ số dưới",
    "Chỉ số trên",
    "Danh sách tác vụ",
    "Căn giữa",
    "Màu chữ",
    "Phông chữ",
    "Công thức",
    "Video YouTube",
    "Emoji",
    "Nhắc người dùng",
    "Ký tự ẩn",
    "Khối thu gọn",
    "Thêm hàng",
    "Thêm cột",
  ]) {
    assert.ok(editorSource.includes(label), `${label} must be available`);
  }
  assert.match(editorSource, /editor\.setEditable\(!readOnly, false\)/);
  assert.match(editorSource, /editor\.storage\.characterCount\.characters\(\)/);
  assert.match(editorSource, /editor\.storage\.characterCount\.words\(\)/);
});
