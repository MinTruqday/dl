import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibLineNumbers implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Line Numbers",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="6" x2="20" y2="6"/><line x1="12" y1="12" x2="20" y2="12"/><line x1="12" y1="18" x2="20" y2="18"/><path d="M4 6h4"/><path d="M4 12h4"/><path d="M4 18h4"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      text: data?.text || "",
      startNumber: data?.startNumber || 1,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-linenum { display: flex; gap: 16px; margin: 16px 0; font-family: monospace; font-size: 14px; line-height: 1.8; }
      .doclib-linenum-gutter { width: 32px; text-align: right; color: #94a3b8; user-select: none; border-right: 1px solid #cbd5e1; padding-right: 8px; display: flex; flex-direction: column; }
      .doclib-linenum-content { flex: 1; outline: none; white-space: pre-wrap; }
      .doclib-linenum-content:empty::before { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; }
      .doclib-linenum-controls { display: flex; gap: 8px; margin-top: 8px; background: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0; }
      .doclib-linenum-input { width: 60px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-linenum");

    const gutter = document.createElement("div");
    gutter.classList.add("doclib-linenum-gutter");

    const content = document.createElement("div");
    content.classList.add("doclib-linenum-content");
    content.innerText = this.data.text;

    const updateGutter = () => {
      const lines = content.innerText.split("\\n").length;
      gutter.innerHTML = "";
      let current = parseInt(this.data.startNumber, 10) || 1;
      for (let i = 0; i < lines; i++) {
        const span = document.createElement("span");
        span.innerText = String(current++);
        gutter.appendChild(span);
      }
    };

    if (!this.readOnly) {
      content.contentEditable = "true";
      content.addEventListener("input", () => {
        this.data.text = content.innerText;
        updateGutter();
      });
    }

    container.appendChild(gutter);
    container.appendChild(content);
    updateGutter();
    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-linenum-controls");

      const label = document.createElement("span");
      label.innerText = "Start:";
      label.style.fontSize = "12px";
      label.style.color = "#64748b";
      label.style.alignSelf = "center";

      const startInput = document.createElement("input");
      startInput.type = "number";
      startInput.classList.add("doclib-linenum-input");
      startInput.value = this.data.startNumber;
      startInput.addEventListener("input", () => {
        this.data.startNumber = startInput.value;
        updateGutter();
      });

      controls.appendChild(label);
      controls.appendChild(startInput);
      this.wrapper.appendChild(controls);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      startNumber: this.data.startNumber,
    };
  }
}
