import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibMath implements BlockTool {
  static readonly feature = {
    id: "DocLibMath",
    title: "DocLib Math",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f821e57a41c9e5dd"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,20 12,7 18,18 12,4 5,20 15,10"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { formula: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Math (KaTeX)",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f821e57a41c9e5dd"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,20 12,7 18,18 12,4 5,20 15,10"/></svg>',
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
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      formula: data.formula || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-math-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-math-styles";
      style.innerHTML = `
            .doclib-math-wrapper { margin: 16px 0; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background: #f8fafc; text-align: center; }
            .doclib-math-display { font-size: 1.5em; min-height: 40px; display: flex; align-items: center; justify-content: center; overflow-x: auto; padding: 12px 0; }
            .doclib-math-input { width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; font-family: monospace; outline: none; margin-top: 16px; font-size: 14px; background: #fff; }
            .doclib-math-input:focus { border-color: #3b82f6; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-math-wrapper");

    const display = document.createElement("div");
    display.classList.add("doclib-math-display");

    const renderMath = () => {
      if ((window as any).katex) {
        try {
          (window as any).katex.render(this.data.formula || " ", display, {
            throwOnError: false,
            displayMode: true,
          });
        } catch (e) {
          display.innerText = this.data.formula;
        }
      } else {
        display.innerText = this.data.formula;
      }
    };

    if (!(window as any).katex) {
      if (!document.getElementById("katex-css")) {
        const link = document.createElement("link");
        link.id = "katex-css";
        link.rel = "stylesheet";
        link.href =
          "https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css";
        document.head.appendChild(link);
      }
      const script = document.createElement("script");
      script.src =
        "https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js";
      script.onload = renderMath;
      document.head.appendChild(script);
    } else {
      renderMath();
    }

    container.appendChild(display);

    if (!this.readOnly) {
      const input = document.createElement("input");
      input.classList.add("doclib-math-input");
      input.value = this.data.formula;
      input.placeholder = "DocLib Code";
      input.addEventListener("input", () => {
        this.data.formula = input.value;
        renderMath();
      });
      container.appendChild(input);
    }

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
