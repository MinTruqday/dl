import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMailMerge implements BlockTool {
  static readonly feature = {
    id: "DocLibMailMerge",
    title: "DocLib Mail Merge",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="69e59677cd0c78d9"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="7,12 18,4 5,16 5,17 17,14 4,18"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Mail Merge",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="69e59677cd0c78d9"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="7,12 18,4 5,16 5,17 17,14 4,18"/></svg>',
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
      field: data?.field || "",
      fallback: data?.fallback || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-mailmerge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 2px 8px;
        font-family: monospace;
        font-size: 13px;
        color: #0f172a;
      }
      .doclib-mailmerge-edit {
        display: flex;
        gap: 8px;
        background: #fff;
        border: 1px solid #cbd5e1;
        padding: 12px;
        border-radius: 6px;
      }
      .doclib-mailmerge-input {
        flex: 1;
        padding: 6px 10px;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        font-size: 13px;
        outline: none;
      }
      .doclib-mailmerge-input:focus {
        border-color: #3b82f6;
      }
    `;
    this.wrapper.appendChild(style);

    if (this.readOnly) {
      const container = document.createElement("span");
      container.classList.add("doclib-mailmerge");
      container.innerText = `${this.data.field || this.data.fallback}`;
      this.wrapper.appendChild(container);
      return this.wrapper;
    }

    const edit = document.createElement("div");
    edit.classList.add("doclib-mailmerge-edit");

    const fieldInput = document.createElement("input");
    fieldInput.classList.add("doclib-mailmerge-input");
    fieldInput.placeholder = "";
    fieldInput.value = this.data.field;
    fieldInput.addEventListener("input", () => {
      this.data.field = fieldInput.value;
    });

    const fallbackInput = document.createElement("input");
    fallbackInput.classList.add("doclib-mailmerge-input");
    fallbackInput.placeholder = "";
    fallbackInput.value = this.data.fallback;
    fallbackInput.addEventListener("input", () => {
      this.data.fallback = fallbackInput.value;
    });

    edit.appendChild(fieldInput);
    edit.appendChild(fallbackInput);
    this.wrapper.appendChild(edit);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      field: this.data.field,
      fallback: this.data.fallback,
    };
  }
}
