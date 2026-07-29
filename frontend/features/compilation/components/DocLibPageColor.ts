import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPageColor implements BlockTool {
  static readonly feature = {
    id: "DocLibPageColor",
    title: "DocLib Page Color",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f972184e18ee8e47"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="15,16 11,14 11,4 10,7 6,13 12,15"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Page Color",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f972184e18ee8e47"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="15,16 11,14 11,4 10,7 6,13 12,15"/></svg>',
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
      color: data?.color || "#ffffff",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-pagecolor { border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; margin: 16px 0; background: #f8fafc; display: flex; align-items: center; justify-content: space-between; }
      .doclib-pagecolor-label { font-weight: 600; color: #475569; font-size: 14px; display: flex; align-items: center; gap: 8px; }
      .doclib-pagecolor-swatch { width: 24px; height: 24px; border-radius: 50%; border: 1px solid #cbd5e1; }
      .doclib-pagecolor-input { border: none; padding: 0; width: 30px; height: 30px; cursor: pointer; outline: none; background: transparent; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-pagecolor");

    const label = document.createElement("div");
    label.classList.add("doclib-pagecolor-label");

    const swatch = document.createElement("div");
    swatch.classList.add("doclib-pagecolor-swatch");

    const updateColor = () => {
      swatch.style.backgroundColor = this.data.color;
      label.innerText = `PAGE COLOR`;
      label.prepend(swatch);

      const editorRoot = document.querySelector(".codex-editor") as HTMLElement;
      if (editorRoot) {
        editorRoot.style.backgroundColor = this.data.color;
        editorRoot.style.transition = "background-color 0.3s";
      }
    };

    updateColor();
    container.appendChild(label);

    if (!this.readOnly) {
      const input = document.createElement("input");
      input.type = "color";
      input.classList.add("doclib-pagecolor-input");
      input.value = this.data.color;
      input.addEventListener("input", () => {
        this.data.color = input.value;
        updateColor();
      });
      container.appendChild(input);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      color: this.data.color,
    };
  }
}
