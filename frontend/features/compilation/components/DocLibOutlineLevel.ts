import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibOutlineLevel implements BlockTool {
  static readonly feature = {
    id: "DocLibOutlineLevel",
    title: "Outline Level",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2ebf3b9fb2cb56f9"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,8 12,10 12,20 5,15 5,4 16,15"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Outline Level",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2ebf3b9fb2cb56f9"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,8 12,10 12,20 5,15 5,4 16,15"/></svg>',
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
      level: data?.level || "Level 1",
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-outline { display: flex; align-items: stretch; gap: 12px; margin: 8px 0; font-family: sans-serif; }
      .doclib-outline-ctrl { display: flex; align-items: center; justify-content: center; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 0 8px; cursor: pointer; user-select: none; }
      .doclib-outline-lvl { font-size: 11px; font-weight: bold; color: #64748b; width: 50px; text-align: center; }
      .doclib-outline-btn { border: none; background: transparent; color: #94a3b8; font-weight: bold; cursor: pointer; padding: 4px; outline: none; }
      .doclib-outline-btn:hover { color: #3b82f6; }
      .doclib-outline-text { flex: 1; font-weight: bold; color: #0f172a; outline: none; display: flex; align-items: center; padding: 8px; border-bottom: 1px dotted transparent; transition: 0.3s; }
      .doclib-outline-text:focus { border-bottom-color: #3b82f6; }
      .doclib-outline-text:empty:before { content: "DocLib Outline Text"; color: #94a3b8; font-weight: normal; font-style: italic; }
      
      .doclib-outline[data-level="Level 1"] .doclib-outline-text { font-size: 24px; }
      .doclib-outline[data-level="Level 2"] .doclib-outline-text { font-size: 20px; margin-left: 24px; }
      .doclib-outline[data-level="Level 3"] .doclib-outline-text { font-size: 18px; margin-left: 48px; }
      .doclib-outline[data-level="Level 4"] .doclib-outline-text { font-size: 16px; margin-left: 72px; }
      .doclib-outline[data-level="Level 5"] .doclib-outline-text { font-size: 14px; margin-left: 96px; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-outline");
    container.dataset.level = this.data.level;

    if (!this.readOnly) {
      const ctrl = document.createElement("div");
      ctrl.classList.add("doclib-outline-ctrl");

      const leftBtn = document.createElement("button");
      leftBtn.classList.add("doclib-outline-btn");
      leftBtn.innerText = "<";

      const lvl = document.createElement("div");
      lvl.classList.add("doclib-outline-lvl");
      lvl.innerText = this.data.level;

      const rightBtn = document.createElement("button");
      rightBtn.classList.add("doclib-outline-btn");
      rightBtn.innerText = ">";

      const updateLevel = (delta: number) => {
        let cur = parseInt(this.data.level.replace("Level ", ""));
        cur += delta;
        if (cur < 1) cur = 1;
        if (cur > 5) cur = 5;
        this.data.level = `Level ${cur}`;
        lvl.innerText = this.data.level;
        container.dataset.level = this.data.level;
      };

      leftBtn.addEventListener("click", () => updateLevel(-1));
      rightBtn.addEventListener("click", () => updateLevel(1));

      ctrl.appendChild(leftBtn);
      ctrl.appendChild(lvl);
      ctrl.appendChild(rightBtn);
      container.appendChild(ctrl);
    }

    const text = document.createElement("div");
    text.classList.add("doclib-outline-text");
    text.innerText = this.data.text;

    if (!this.readOnly) {
      text.contentEditable = "true";
      text.addEventListener("input", () => {
        this.data.text = text.innerText;
      });
    }
    container.appendChild(text);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
