import type { OutputData } from "@editorjs/editorjs";

const CODE_BLOCK_TYPES = new Set([
  "code",
  "codeBox",
  "codeMirror",
  "jsonViewer",
  "latex",
  "markdownBlock",
  "mermaid",
  "monacoLatex",
]);

const MARKUP_FIELDS = new Set([
  "caption",
  "content",
  "description",
  "html",
  "label",
  "result",
  "text",
  "title",
]);

const SAFE_DATA_IMAGE =
  /^data:image\/(?:gif|jpeg|png|webp);base64,[a-z0-9+/=\s]+$/i;

export function sanitizeEditorMarkup(value: string): string {
  if (typeof document === "undefined" || !value) return value;
  const template = document.createElement("template");
  template.innerHTML = value;
  template.content
    .querySelectorAll(
      "script,style,iframe,object,embed,link,meta,base,form",
    )
    .forEach((element) => element.remove());
  template.content.querySelectorAll("*").forEach((element) => {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase();
      const normalizedValue = attribute.value.trim().toLowerCase();
      if (
        name.startsWith("on") ||
        name === "srcdoc" ||
        (name === "style" &&
          /(expression|url\s*\(|@import|-moz-binding)/i.test(attribute.value)) ||
        (["href", "src", "xlink:href"].includes(name) &&
          (normalizedValue.startsWith("javascript:") ||
            (normalizedValue.startsWith("data:") &&
              !SAFE_DATA_IMAGE.test(attribute.value))))
      ) {
        element.removeAttribute(attribute.name);
      }
    }
    if (
      element.getAttribute("target") === "_blank" &&
      !element.getAttribute("rel")
    ) {
      element.setAttribute("rel", "noopener noreferrer");
    }
  });
  return template.innerHTML;
}

function sanitizeValue(value: unknown, key: string): unknown {
  if (typeof value === "string") {
    return MARKUP_FIELDS.has(key) ? sanitizeEditorMarkup(value) : value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeValue(item, key));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([childKey, childValue]) => [
        childKey,
        sanitizeValue(childValue, childKey),
      ]),
    );
  }
  return value;
}

export function sanitizeEditorData(data: OutputData): OutputData {
  return {
    ...data,
    blocks: data.blocks.map((block) => {
      if (CODE_BLOCK_TYPES.has(block.type)) return block;
      return {
        ...block,
        data: sanitizeValue(block.data, "") as Record<string, unknown>,
      };
    }),
  };
}
