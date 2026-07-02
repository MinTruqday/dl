import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDocumentProperty implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Document Property",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>',
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
