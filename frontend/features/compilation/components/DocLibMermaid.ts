import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibMermaid implements BlockTool {
  static readonly feature = {
    id: "DocLibMermaid",
    title: "DocLib Mermaid",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="cc3114cfadd78f92"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="4,19 7,7 7,15 11,14 19,18 16,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Mermaid",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="cc3114cfadd78f92"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="4,19 7,7 7,15 11,14 19,18 16,19"/></svg>',
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
      code: data?.code || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-mermaid-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-mermaid-styles";
      style.innerHTML = `
        .doclib-mermaid-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 10px 0; }
        .doclib-mermaid-textarea { width: 100%; min-height: 120px; padding: 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; border: none; border-bottom: 1px solid #e2e8f0; outline: none; resize: vertical; background: #f8fafc; font-size: 14px; line-height: 1.5; box-sizing: border-box; }
        .doclib-mermaid-preview { padding: 24px; text-align: center; background: white; min-height: 120px; display: flex; justify-content: center; align-items: center; overflow-x: auto; }
        .doclib-mermaid-error { color: #ef4444; font-weight: 500; font-size: 13px; padding: 12px; }
      `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-mermaid-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private loadMermaid(): Promise<any> {
    return new Promise((resolve) => {
      if ((window as any).mermaid) {
        resolve((window as any).mermaid);
        return;
      }
      if (document.getElementById("mermaid-script")) {
        window.addEventListener(
          "mermaid-loaded",
          () => resolve((window as any).mermaid),
          { once: true },
        );
        return;
      }
      const script = document.createElement("script");
      script.id = "mermaid-script";
      script.src =
        "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
      script.onload = () => {
        (window as any).mermaid.initialize({
          startOnLoad: false,
          theme: "default",
        });
        window.dispatchEvent(new Event("mermaid-loaded"));
        resolve((window as any).mermaid);
      };
      document.head.appendChild(script);
    });
  }

  private async renderPreview(code: string, preview: HTMLElement) {
    preview.innerHTML = "";
    const id = `mermaid-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
    try {
      const mermaid = await this.loadMermaid();
      const container = document.createElement("div");
      container.id = id;
      preview.appendChild(container);
      const { svg } = await mermaid.render(id, code);
      container.innerHTML = svg;
    } catch (e) {
      preview.innerHTML = `<div class="doclib-mermaid-error">Mermaid Syntax Error</div>`;
    }
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const preview = document.createElement("div");
    preview.classList.add("doclib-mermaid-preview");

    if (this.readOnly) {
      this.wrapper.appendChild(preview);
      this.renderPreview(this.data.code, preview);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.classList.add("doclib-mermaid-textarea");
    textarea.value = this.data.code;
    textarea.placeholder = "DocLib Code";

    let timeout: ReturnType<typeof setTimeout>;
    textarea.addEventListener("input", () => {
      this.data.code = textarea.value;
      clearTimeout(timeout);
      timeout = setTimeout(
        () => this.renderPreview(this.data.code, preview),
        600,
      );
    });

    this.wrapper.appendChild(textarea);
    this.wrapper.appendChild(preview);
    this.renderPreview(this.data.code, preview);
  }

  save() {
    return this.data;
  }
}
