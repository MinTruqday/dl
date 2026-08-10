import edjsHTML from "editorjs-html";

const parsers = {
  alert: (block: any) =>
    `<aside class="my-4 rounded-control bg-surface-quiet p-4"><strong>${block.data.type || "Lưu ý"}</strong><div>${block.data.message || ""}</div></aside>`,
  table: (block: any) =>
    `<table class="my-4 w-full border-collapse">${(block.data.content || []).map((row: any[]) => `<tr>${row.map((cell) => `<td class="border border-border p-2">${cell}</td>`).join("")}</tr>`).join("")}</table>`,
  toggle: (block: any) =>
    `<details class="my-4 rounded-control border border-border p-4"><summary class="cursor-pointer font-semibold">${block.data.text || "Chi tiết"}</summary><div class="mt-2">${block.data.items || ""}</div></details>`,
  checklist: (block: any) =>
    `<ul class="my-4 space-y-2">${(block.data.items || []).map((item: any) => `<li>${item.checked ? "Đã chọn" : "Chưa chọn"} ${item.text || ""}</li>`).join("")}</ul>`,
  nestedChecklist: (block: any) =>
    `<ul class="my-4 space-y-2">${(block.data.items || []).map((item: any) => `<li>${item.checked ? "Đã chọn" : "Chưa chọn"} ${item.content || ""}</li>`).join("")}</ul>`,
  originalQuote: (block: any) =>
    `<blockquote class="my-4 border-l-2 border-border-strong py-2 pl-4">${block.data.text || ""}<cite class="mt-2 block text-[13px] text-ink-muted">${block.data.caption || ""}</cite></blockquote>`,
  divider: () => `<hr class="my-6 border-border" />`,
  math: (block: any) =>
    `<pre class="my-4 overflow-x-auto rounded-control bg-surface-quiet p-4">${block.data.math || ""}</pre>`,
  mermaid: () =>
    `<div class="my-4 rounded-control border border-border p-4 text-ink-muted">Biểu đồ chưa có bản xem trước</div>`,
  attaches: (block: any) =>
    `<div class="my-4 rounded-control border border-border p-4"><strong>${block.data.title || "Tệp đính kèm"}</strong><div>${block.data.file?.url || ""}</div></div>`,
  personality: (block: any) =>
    `<div class="my-4 border-y border-border py-4"><strong>${block.data.name || ""}</strong><div>${block.data.description || ""}</div></div>`,
};

const parser = edjsHTML(parsers);
const supported = new Set([
  "paragraph",
  "header",
  "list",
  "quote",
  "image",
  "delimiter",
  ...Object.keys(parsers),
]);

export function renderEditorPreview(content: string) {
  if (!content.trim()) return "";
  try {
    const data = JSON.parse(content);
    if (!Array.isArray(data.blocks)) return content;
    const normalized = {
      ...data,
      blocks: data.blocks.filter((block: any) => supported.has(block.type)),
    };
    const result = parser.parse(normalized);
    return Array.isArray(result) ? result.join("") : result;
  } catch {
    return content;
  }
}
