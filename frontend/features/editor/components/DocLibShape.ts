import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibShape implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Shape",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><path d="M14 3h7v7h-7z"/><path d=\"M14 14h7v7h-7z\"/><circle cx="6.5" cy="17.5" r="3.5"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      shape: data?.shape || "",
      fill: data?.fill || "",
      stroke: data?.stroke || "",
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-shape-wrap { display: flex; flex-direction: column; align-items: center; margin: 24px 0; }
      .doclib-shape-svg { width: 150px; height: 150px; position: relative; display: flex; align-items: center; justify-content: center; }
      .doclib-shape-svg svg { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; }
      .doclib-shape-text { position: relative; z-index: 2; color: #fff; font-weight: 600; text-align: center; max-width: 80%; outline: none; }
      .doclib-shape-text:empty::before { content: "DocLib Text"; color: rgba(255,255,255,0.6); pointer-events: none; }
      
      .doclib-shape-controls { display: flex; gap: 8px; margin-top: 16px; background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; }
      .doclib-shape-select, .doclib-shape-color { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-shape-wrap");

    const svgWrap = document.createElement("div");
    svgWrap.classList.add("doclib-shape-svg");

    const textEl = document.createElement("div");
    textEl.classList.add("doclib-shape-text");
    textEl.innerText = this.data.text;

    if (!this.readOnly) {
      textEl.contentEditable = "true";
      textEl.addEventListener("input", () => { this.data.text = textEl.innerText; });
    }

    const renderShape = () => {
      let path = "";
      if (this.data.shape === "rectangle") path = '<rect x="10" y="10" width="80" height="80" rx="8" />';
      else if (this.data.shape === "circle") path = '<circle cx="50" cy="50" r="40" />';
      else if (this.data.shape === "triangle") path = '<polygon points="50,10 90,90 10,90" />';
      else if (this.data.shape === "diamond") path = '<polygon points="50,10 90,50 50,90 10,50" />';
      else if (this.data.shape === "star") path = '<polygon points="50,10 61,35 88,35 66,51 74,76 50,60 26,76 34,51 12,35 39,35" />';
      else if (this.data.shape === "arrow") path = '<polygon points="10,40 50,40 50,20 90,50 50,80 50,60 10,60" />';

      svgWrap.innerHTML = `<svg viewBox="0 0 100 100" fill="${this.data.fill}" stroke="${this.data.stroke}" stroke-width="2">${path}</svg>`;
      svgWrap.appendChild(textEl);
    };

    renderShape();
    container.appendChild(svgWrap);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-shape-controls");

      const select = document.createElement("select");
      select.classList.add("doclib-shape-select");
      ["rectangle", "circle", "triangle", "diamond", "star", "arrow"].forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.text = s.charAt(0).toUpperCase() + s.slice(1);
        opt.selected = this.data.shape === s;
        select.appendChild(opt);
      });
      select.addEventListener("change", () => { this.data.shape = select.value; renderShape(); });

      const fillInput = document.createElement("input");
      fillInput.type = "color";
      fillInput.classList.add("doclib-shape-color");
      fillInput.value = this.data.fill;
      fillInput.addEventListener("input", () => { this.data.fill = fillInput.value; renderShape(); });

      controls.appendChild(select);
      controls.appendChild(fillInput);
      container.appendChild(controls);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      shape: this.data.shape,
      fill: this.data.fill,
      stroke: this.data.stroke,
      text: this.data.text,
    };
  }
}
