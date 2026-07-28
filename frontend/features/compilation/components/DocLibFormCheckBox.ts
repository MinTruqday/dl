import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormCheckBox implements BlockTool {
  static readonly feature = {
    id: "DocLibFormCheckBox",
    title: "DocLib FormCheckBox",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="10b6049272e0d6f0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="20,16 8,14 16,7 14,6 7,20 10,4"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form CheckBox",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="10b6049272e0d6f0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="20,16 8,14 16,7 14,6 7,20 10,4"/></svg>',
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
      label: data?.label || "DocLib Button",
      checked: data?.checked || false,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-form-cb { display: flex; align-items: center; gap: 12px; margin: 12px 0; padding: 8px 12px; border: 1px solid transparent; border-radius: 4px; transition: background 0.2s; }
      .doclib-form-cb:hover { background: #f8fafc; border-color: #e2e8f0; }
      .doclib-form-cb-input { width: 20px; height: 20px; cursor: pointer; accent-color: #2563eb; margin: 0; }
      .doclib-form-cb-label { flex: 1; font-size: 15px; color: #1e293b; outline: none; }
      .doclib-form-cb-label:empty::before { content: "DocLib Text"; color: #94a3b8; pointer-events: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("label");
    container.classList.add("doclib-form-cb");

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.classList.add("doclib-form-cb-input");
    cb.checked = this.data.checked;
    cb.addEventListener("change", () => {
      this.data.checked = cb.checked;
    });

    const label = document.createElement("div");
    label.classList.add("doclib-form-cb-label");
    label.innerText = this.data.label;

    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
      cb.addEventListener("click", (e) => {
        if (!this.readOnly && document.activeElement === label) {
          e.preventDefault();
        }
      });
    }

    container.appendChild(cb);
    container.appendChild(label);
    this.wrapper.appendChild(container);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      label: this.data.label,
      checked: this.data.checked,
    };
  }
}
