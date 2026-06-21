import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMailMerge implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Mail Merge Field",
      icon: "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z\"/><polyline points=\"22,6 12,13 2,6\"/></svg>",
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
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
    fieldInput.placeholder = "Merge Field eg FirstName";
    fieldInput.value = this.data.field;
    fieldInput.addEventListener("input", () => {
      this.data.field = fieldInput.value;
    });

    const fallbackInput = document.createElement("input");
    fallbackInput.classList.add("doclib-mailmerge-input");
    fallbackInput.placeholder = "Fallback eg Customer";
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
