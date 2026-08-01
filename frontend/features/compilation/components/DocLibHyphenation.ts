import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibHyphenation implements BlockTool {
  static readonly feature = {
    id: "DocLibHyphenation",
    title: "DocLib Hyphenation",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="89d2cc9be884da75"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,10 4,6 15,17 18,19 8,16 14,6"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Hyphenation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="89d2cc9be884da75"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,10 4,6 15,17 18,19 8,16 14,6"/></svg>',
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
      .doclib-hyph { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid hsl(var(--border)); border-radius: 4px; background: hsl(var(--surface)); margin: 16px 0; max-width: 300px; font-family: sans-serif; }
      .doclib-hyph-title { font-size: 14px; font-weight: bold; color: hsl(var(--ink)); display: flex; align-items: center; gap: 8px; }
      .doclib-hyph-title::before { content: "ABC-"; color: hsl(var(--brand)); font-family: monospace; font-weight: bold; }
      .doclib-hyph-select { padding: 6px 12px; border: 1px solid hsl(var(--border)); border-radius: 4px; background: hsl(var(--surface-raised)); outline: none; font-size: 13px; cursor: pointer; }
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
