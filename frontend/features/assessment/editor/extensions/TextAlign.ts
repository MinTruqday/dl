import { Extension } from "@tiptap/core";

export const TextAlign = Extension.create({
  name: "textAlign",
  addGlobalAttributes() {
    return [{
      types: ["heading", "paragraph"],
      attributes: {
        textAlign: {
          default: "left",
          parseHTML: (element: HTMLElement) => element.style.textAlign || "left",
          renderHTML: (attributes: Record<string, unknown>) => attributes.textAlign === "left" ? {} : { style: `text-align: ${String(attributes.textAlign)}` },
        },
      },
    }];
  },
});
