import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSectionBreak implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Section Break",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="12" x2="20" y2="12" stroke-dasharray="4 4"/><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="18" x2="20" y2="18"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      type: data?.type || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-sbreak { border-top: 2px dashed #94a3b8; margin: 32px 0; position: relative; text-align: center; }
      .doclib-sbreak-label { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #fff; padding: 0 12px; font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.1em; }
      .doclib-sbreak-select { position: absolute; top: 12px; left: 50%; transform: translateX(-50%); padding: 4px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; background: #f8fafc; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-sbreak");
    
    const label = document.createElement("div");
    label.classList.add("doclib-sbreak-label");
    
    const updateLabel = () => {
      label.innerText = `SECTION BREAK (${this.data.type.toUpperCase()})`;
      if (this.data.type === "next-page") {
        container.style.pageBreakAfter = "always";
      } else {
        container.style.pageBreakAfter = "auto";
      }
    };
    updateLabel();
    
    container.appendChild(label);

    if (!this.readOnly) {
      const select = document.createElement("select");
      select.classList.add("doclib-sbreak-select");
      ["continuous", "next-page", "even-page", "odd-page"].forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.text = t;
        opt.selected = this.data.type === t;
        select.appendChild(opt);
      });
      select.addEventListener("change", () => {
        this.data.type = select.value;
        updateLabel();
      });
      container.appendChild(select);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      type: this.data.type,
    };
  }
}
