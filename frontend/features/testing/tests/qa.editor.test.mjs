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
    "font-family",
    "highlight",
    "image",
    "link",
    "mathematics",
    "placeholder",
    "subscript",
    "superscript",
    "table",
    "table-cell",
    "table-header",
    "table-row",
    "task-item",
    "task-list",
    "text-align",
    "text-style",
    "typography",
    "underline",
  ];

  for (const name of packages) {
    assert.match(extensionSource, new RegExp(`@tiptap/extension-${name}`));
  }
  assert.match(extensionSource, /StarterKit\.configure\(\{ codeBlock: false \}\)/);
  assert.match(extensionSource, /CodeBlockLowlight\.configure\(\{ lowlight \}\)/);
  assert.match(extensionSource, /openOnClick: !editable/);
  assert.match(extensionSource, /Table\.configure\(\{ resizable: editable \}\)/);
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
