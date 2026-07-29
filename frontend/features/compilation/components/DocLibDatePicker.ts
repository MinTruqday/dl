import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDatePicker implements BlockTool {
  static readonly feature = {
    id: "DocLibDatePicker",
    title: "DocLib Date Picker",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8d57185f921d5697"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="9,6 11,14 14,16 5,19 12,7 15,12"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Date Picker",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8d57185f921d5697"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="9,6 11,14 14,16 5,19 12,7 15,12"/></svg>',
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
      label: data?.label || "",
      date: data?.date || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-dp { font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin: 16px 0; max-width: 300px; }
      .doclib-dp-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-dp-label:empty:before { content: "DocLib Date Label"; color: #94a3b8; font-weight: normal; }
      .doclib-dp-input { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; color: #0f172a; outline: none; background: #fff; cursor: pointer; }
      .doclib-dp-input:focus { border-color: #3b82f6; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-dp");

    const label = document.createElement("div");
    label.classList.add("doclib-dp-label");
    label.innerText = this.data.label;
    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
    }
    container.appendChild(label);

    const input = document.createElement("input");
    input.type = "date";
    input.classList.add("doclib-dp-input");
    input.value = this.data.date;
    if (this.readOnly) input.disabled = true;

    if (!this.readOnly) {
      input.addEventListener("change", () => {
        this.data.date = input.value;
      });
    }

    container.appendChild(input);
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
