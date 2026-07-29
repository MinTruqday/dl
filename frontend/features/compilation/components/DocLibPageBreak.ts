import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPageBreak implements BlockTool {
  static readonly feature = {
    id: "DocLibPageBreak",
    title: "Page Break",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca59aa56b42b1f64"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="19,8 4,5 14,13 18,19 19,16 10,13"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Page Break",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca59aa56b42b1f64"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="19,8 4,5 14,13 18,19 19,16 10,13"/></svg>',
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
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-page-break {
        display: flex;
        align-items: center;
        text-align: center;
        color: #94a3b8;
        margin: 24px 0;
        page-break-after: always;
        break-after: page;
      }
      .doclib-page-break::before, .doclib-page-break::after {
        content: "";
        flex: 1;
        border-bottom: 1px dashed #cbd5e1;
      }
      .doclib-page-break:not(.read-only)::before, .doclib-page-break:not(.read-only)::after {
        border-bottom: 1px dashed #94a3b8;
      }
      .doclib-page-break-text {
        padding: 0 16px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
      }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-page-break");
    if (this.readOnly) {
      container.classList.add("read-only");
    }

    const text = document.createElement("div");
    text.classList.add("doclib-page-break-text");
    text.innerText = "Page Break";

    container.appendChild(text);
    this.wrapper.appendChild(container);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {};
  }
}
