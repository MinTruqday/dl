import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibHyphenation implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Hyphenation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16"></path><path d="M4 6h16"></path><path d="M4 18h16"></path></svg>',
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
      mode: data?.mode || "None",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-hyph { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 4px; background: #fff; margin: 16px 0; max-width: 300px; font-family: sans-serif; }
      .doclib-hyph-title { font-size: 14px; font-weight: bold; color: #1e293b; display: flex; align-items: center; gap: 8px; }
      .doclib-hyph-title::before { content: "ABC-"; color: #3b82f6; font-family: monospace; font-weight: bold; }
      .doclib-hyph-select { padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; outline: none; font-size: 13px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-hyph");

    const title = document.createElement("div");
    title.classList.add("doclib-hyph-title");
    title.innerText = "Hyphenation";
    container.appendChild(title);

    const select = document.createElement("select");
    select.classList.add("doclib-hyph-select");
    if (this.readOnly) select.disabled = true;

    ["None", "Automatic", "Manual"].forEach((opt) => {
      const option = document.createElement("option");
      option.value = opt;
      option.innerText = opt;
      if (this.data.mode === opt) option.selected = true;
      select.appendChild(option);
    });

    if (!this.readOnly) {
      select.addEventListener("change", () => {
        this.data.mode = select.value;
      });
    }

    container.appendChild(select);
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
