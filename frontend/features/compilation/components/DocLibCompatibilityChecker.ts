import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCompatibilityChecker implements BlockTool {
  static readonly feature = {
    id: "DocLibCompatibilityChecker",
    title: "DocLib CompatibilityChecker",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9131d5cea557438b"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="13,19 13,6 16,6 20,7 14,14 18,17"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Compatibility Checker",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9131d5cea557438b"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="13,19 13,6 16,6 20,7 14,14 18,17"/></svg>',
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
      issues:
        data?.issues && data.issues.length > 0
          ? data.issues
          : ["DocLib Issue: Text effects will be removed in older versions."],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-compat { font-family: sans-serif; padding: 16px; border: 1px solid hsl(var(--warning-soft)); border-radius: 8px; background: #fffbeb; margin: 16px 0; max-width: 500px; display: flex; flex-direction: column; gap: 8px; }
      .doclib-compat-head { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 16px; color: #b45309; border-bottom: 1px solid #fde68a; padding-bottom: 8px; }
      .doclib-compat-icon { width: 24px; height: 24px; color: hsl(var(--warning)); }
      .doclib-compat-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
      .doclib-compat-item { display: flex; align-items: flex-start; gap: 8px; font-size: 14px; color: #92400e; position: relative; }
      .doclib-compat-item::before { content: "•"; color: hsl(var(--warning)); font-weight: bold; }
      .doclib-compat-text { flex: 1; outline: none; }
      .doclib-compat-text:empty:before { content: "DocLib Compatibility Issue"; color: hsl(var(--warning-soft)); }
      .doclib-compat-del { font-size: 10px; color: hsl(var(--danger)); border: none; background: transparent; cursor: pointer; display: none; }
      .doclib-compat-item:hover .doclib-compat-del { display: block; }
      .doclib-compat-add { padding: 8px; background: transparent; border: 1px dashed hsl(var(--warning-soft)); border-radius: 4px; color: hsl(var(--warning)); text-align: center; font-size: 12px; cursor: pointer; font-weight: bold; }
      .doclib-compat-add:hover { background: #fef3c7; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-compat");

    const head = document.createElement("div");
    head.classList.add("doclib-compat-head");
    head.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9131d5cea557438b"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="13,19 13,6 16,6 20,7 14,14 18,17"/></svg> <span>Compatibility Checker</span>`;
    container.appendChild(head);

    const list = document.createElement("div");
    list.classList.add("doclib-compat-list");
    container.appendChild(list);

    const renderList = () => {
      list.innerHTML = "";
      this.data.issues.forEach((issue: string, i: number) => {
        const item = document.createElement("div");
        item.classList.add("doclib-compat-item");

        const text = document.createElement("div");
        text.classList.add("doclib-compat-text");
        text.innerText = issue;

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", () => {
            this.data.issues[i] = text.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-compat-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.issues.splice(i, 1);
            renderList();
          });
          item.appendChild(text);
          item.appendChild(del);
        } else {
          item.appendChild(text);
        }

        list.appendChild(item);
      });
    };

    renderList();

    if (!this.readOnly) {
      const add = document.createElement("button");
      add.classList.add("doclib-compat-add");
      add.innerText = "+ Add Issue";
      add.addEventListener("click", () => {
        this.data.issues.push("DocLib New Issue");
        renderList();
      });
      container.appendChild(add);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
