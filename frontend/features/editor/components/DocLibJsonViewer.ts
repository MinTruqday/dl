import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibJsonViewer implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Json Viewer",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
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
      jsonStr:
        data?.jsonStr ||
        `{
  "doclib": "awesome",
  "version": 1
}`,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-json { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; color: #0f172a; position: relative; }
      .doclib-json-textarea { width: 100%; min-height: 150px; background: transparent; border: none; font-family: inherit; font-size: inherit; resize: vertical; outline: none; line-height: 1.5; color: #0f172a; }
      .doclib-json-label { position: absolute; top: -10px; right: 16px; background: #f59e0b; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-family: sans-serif; font-weight: bold; }
      .doclib-json-error { color: #ef4444; font-size: 11px; margin-top: 8px; font-family: sans-serif; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-json");

    const label = document.createElement("div");
    label.classList.add("doclib-json-label");
    label.innerText = "JSON";
    container.appendChild(label);

    const errorMsg = document.createElement("div");
    errorMsg.classList.add("doclib-json-error");

    if (!this.readOnly) {
      const textarea = document.createElement("textarea");
      textarea.classList.add("doclib-json-textarea");
      textarea.value = this.data.jsonStr;
      textarea.spellcheck = false;
      textarea.addEventListener("input", () => {
        this.data.jsonStr = textarea.value;
        try {
          JSON.parse(this.data.jsonStr);
          errorMsg.innerText = "";
        } catch (e: any) {
          errorMsg.innerText = "Invalid JSON: " + e.message;
        }
      });
      container.appendChild(textarea);
      container.appendChild(errorMsg);
    } else {
      const view = document.createElement("pre");
      view.style.margin = "0";
      try {
        const obj = JSON.parse(this.data.jsonStr);
        view.innerText = JSON.stringify(obj, null, 2);
      } catch (e) {
        view.innerText = this.data.jsonStr;
      }
      container.appendChild(view);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
