import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibWordArt implements BlockTool {
  static readonly feature = {
    id: "DocLibWordArt",
    title: "DocLib WordArt",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="867d58f8a15836b5"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="19,10 7,14 12,7 7,15 7,13 11,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib WordArt",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="867d58f8a15836b5"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="19,10 7,14 12,7 7,15 7,13 11,4"/></svg>',
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
      text: data?.text || "",
      styleId: data?.styleId || "style1",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-wordart-wrap { text-align: center; margin: 32px 0; }
      .doclib-wordart { font-size: 64px; font-weight: 900; outline: none; min-height: 80px; display: inline-block; padding: 16px; }
      .doclib-wordart:empty::before { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; }
      
      .doclib-wordart.style1 { color: transparent; -webkit-text-stroke: 2px #2563eb; text-shadow: 4px 4px 0px #bfdbfe; }
      .doclib-wordart.style2 { background: linear-gradient(to right, #ec4899, #8b5cf6); -webkit-background-clip: text; color: transparent; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
      .doclib-wordart.style3 { color: #f59e0b; text-shadow: -2px -2px 0 #fff, 2px -2px 0 #fff, -2px 2px 0 #fff, 2px 2px 0 #fff, 4px 4px 0 #b45309; }
      .doclib-wordart.style4 { color: #10b981; transform: skewX(-15deg); text-shadow: 1px 1px 0 #059669, 2px 2px 0 #059669, 3px 3px 0 #059669, 4px 4px 0 #059669; }

      .doclib-wordart-controls { display: flex; gap: 8px; justify-content: center; margin-top: 16px; background: #f8fafc; padding: 8px; border-radius: 8px; border: 1px solid #e2e8f0; }
      .doclib-wordart-select { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-wordart-wrap");

    const textEl = document.createElement("div");
    textEl.classList.add("doclib-wordart", this.data.styleId);
    textEl.innerText = this.data.text;

    if (!this.readOnly) {
      textEl.contentEditable = "true";
      textEl.addEventListener("input", () => {
        this.data.text = textEl.innerText;
      });
    }

    container.appendChild(textEl);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-wordart-controls");

      const select = document.createElement("select");
      select.classList.add("doclib-wordart-select");
      [
        { id: "style1", label: "Outline Shadow" },
        { id: "style2", label: "Gradient" },
        { id: "style3", label: "Retro 3D" },
        { id: "style4", label: "Skewed Block" },
      ].forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.text = s.label;
        opt.selected = this.data.styleId === s.id;
        select.appendChild(opt);
      });

      select.addEventListener("change", () => {
        textEl.classList.remove(this.data.styleId);
        this.data.styleId = select.value;
        textEl.classList.add(this.data.styleId);
      });

      controls.appendChild(select);
      container.appendChild(controls);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      styleId: this.data.styleId,
    };
  }
}
