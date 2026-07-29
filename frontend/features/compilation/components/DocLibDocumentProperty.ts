import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDocumentProperty implements BlockTool {
  static readonly feature = {
    id: "DocLibDocumentProperty",
    title: "Document Property",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a597c99250aaf709"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="16,19 18,14 16,4 13,13 15,17 20,16"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Document Property",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a597c99250aaf709"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="16,19 18,14 16,4 13,13 15,17 20,16"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      propertyType: data?.propertyType || "Author",
      value: data?.value || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-prop { display: inline-flex; align-items: center; gap: 8px; padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; font-family: sans-serif; font-size: 14px; margin: 4px 0; }
      .doclib-prop-type { font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase; user-select: none; }
      .doclib-prop-val { color: #0f172a; min-width: 50px; outline: none; }
      .doclib-prop-val:empty:before { content: "DocLib Value"; color: #94a3b8; font-style: italic; }
      .doclib-prop-select { font-weight: bold; color: #64748b; font-size: 12px; text-transform: uppercase; border: none; background: transparent; outline: none; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-prop");

    if (!this.readOnly) {
      const select = document.createElement("select");
      select.classList.add("doclib-prop-select");
      ["Author", "Title", "Subject", "Company", "Keywords"].forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.innerText = opt;
        if (this.data.propertyType === opt) o.selected = true;
        select.appendChild(o);
      });
      select.addEventListener("change", () => {
        this.data.propertyType = select.value;
      });
      container.appendChild(select);
    } else {
      const type = document.createElement("div");
      type.classList.add("doclib-prop-type");
      type.innerText = this.data.propertyType;
      container.appendChild(type);
    }

    const val = document.createElement("div");
    val.classList.add("doclib-prop-val");
    val.innerText = this.data.value;
    if (!this.readOnly) {
      val.contentEditable = "true";
      val.addEventListener("input", () => {
        this.data.value = val.innerText;
      });
    }
    container.appendChild(val);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
