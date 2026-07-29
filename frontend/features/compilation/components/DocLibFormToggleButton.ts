import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormToggleButton implements BlockTool {
  static readonly feature = {
    id: "DocLibFormToggleButton",
    title: "DocLib Form Toggle Button",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b668a2c6e2ee2aee"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="16,6 13,15 9,4 12,4 8,14 13,5"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form Toggle Button",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b668a2c6e2ee2aee"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="16,6 13,15 9,4 12,4 8,14 13,5"/></svg>',
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
      label: data?.label || "",
      active: data?.active || false,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-toggle { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px 0; max-width: 400px; font-family: sans-serif; cursor: pointer; user-select: none; }
      .doclib-toggle-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; flex: 1; }
      .doclib-toggle-label:empty:before { content: "DocLib Toggle Setting"; color: #94a3b8; font-weight: normal; }
      .doclib-toggle-track { width: 44px; height: 24px; background: #cbd5e1; border-radius: 12px; position: relative; transition: background 0.3s; flex-shrink: 0; }
      .doclib-toggle-track.active { background: #10b981; }
      .doclib-toggle-thumb { width: 20px; height: 20px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: transform 0.3s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .doclib-toggle-track.active .doclib-toggle-thumb { transform: translateX(20px); }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-toggle");

    const label = document.createElement("div");
    label.classList.add("doclib-toggle-label");
    label.innerText = this.data.label;
    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", (e) => {
        e.stopPropagation();
        this.data.label = label.innerText;
      });
      label.addEventListener("click", (e) => e.stopPropagation());
    }
    container.appendChild(label);

    const track = document.createElement("div");
    track.classList.add("doclib-toggle-track");
    if (this.data.active) track.classList.add("active");

    const thumb = document.createElement("div");
    thumb.classList.add("doclib-toggle-thumb");
    track.appendChild(thumb);

    container.appendChild(track);

    if (!this.readOnly) {
      container.addEventListener("click", () => {
        this.data.active = !this.data.active;
        if (this.data.active) track.classList.add("active");
        else track.classList.remove("active");
      });
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
