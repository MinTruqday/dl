import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibJsonViewer implements BlockTool {
  static readonly feature = {
    id: "DocLibJsonViewer",
    title: "DocLib JsonViewer",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9cd9ab22d45b01d6"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="7,17 5,4 12,10 5,14 9,4 8,13"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Json Viewer",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9cd9ab22d45b01d6"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="7,17 5,4 12,10 5,14 9,4 8,13"/></svg>',
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
      .doclib-json { background: hsl(var(--surface-raised)); border: 1px solid hsl(var(--border)); border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; color: hsl(var(--ink)); position: relative; }
      .doclib-json-textarea { width: 100%; min-height: 150px; background: transparent; border: none; font-family: inherit; font-size: inherit; resize: vertical; outline: none; line-height: 1.5; color: hsl(var(--ink)); }
      .doclib-json-label { position: absolute; top: -10px; right: 16px; background: hsl(var(--warning)); color: hsl(var(--surface)); padding: 2px 8px; border-radius: 12px; font-size: 10px; font-family: sans-serif; font-weight: bold; }
      .doclib-json-error { color: hsl(var(--danger)); font-size: 11px; margin-top: 8px; font-family: sans-serif; }
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
