import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMarkdownBlock implements BlockTool {
  static readonly feature = {
    id: "DocLibMarkdownBlock",
    title: "DocLib MarkdownBlock",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c8501fd2c95b99b6"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="17,16 18,10 18,10 4,16 10,11 17,16"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Markdown Block",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c8501fd2c95b99b6"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="17,16 18,10 18,10 4,16 10,11 17,16"/></svg>',
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
      md: data?.md || `# DocLib Markdown\n\nType your **markdown** here.`,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-md { display: flex; flex-direction: column; gap: 8px; font-family: sans-serif; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; }
      .doclib-md-tabs { display: flex; background: #f8fafc; border-bottom: 1px solid #cbd5e1; }
      .doclib-md-tab { padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: bold; color: #64748b; }
      .doclib-md-tab.active { background: #fff; color: #0f172a; border-bottom: 2px solid #3b82f6; }
      .doclib-md-content { padding: 16px; min-height: 150px; }
      .doclib-md-textarea { width: 100%; height: 100%; min-height: 150px; background: transparent; border: none; font-family: monospace; font-size: 14px; resize: vertical; outline: none; line-height: 1.5; color: #0f172a; }
      .doclib-md-preview { font-family: sans-serif; }
      .doclib-md-preview h1 { font-size: 2em; margin-bottom: 0.5em; }
      .doclib-md-preview h2 { font-size: 1.5em; margin-bottom: 0.5em; }
      .doclib-md-preview p { margin-bottom: 1em; }
      .doclib-md-preview strong { font-weight: bold; }
      .doclib-md-preview em { font-style: italic; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-md");

    let isEditMode = !this.readOnly;

    const tabs = document.createElement("div");
    tabs.classList.add("doclib-md-tabs");

    const editTab = document.createElement("div");
    editTab.classList.add("doclib-md-tab");
    editTab.innerText = "Edit";

    const prevTab = document.createElement("div");
    prevTab.classList.add("doclib-md-tab");
    prevTab.innerText = "Preview";

    if (!this.readOnly) {
      tabs.appendChild(editTab);
      tabs.appendChild(prevTab);
      container.appendChild(tabs);
    }

    const contentArea = document.createElement("div");
    contentArea.classList.add("doclib-md-content");
    container.appendChild(contentArea);

    const renderUI = () => {
      contentArea.innerHTML = "";
      if (isEditMode) {
        editTab.classList.add("active");
        prevTab.classList.remove("active");

        const textarea = document.createElement("textarea");
        textarea.classList.add("doclib-md-textarea");
        textarea.value = this.data.md;
        textarea.addEventListener("input", () => {
          this.data.md = textarea.value;
        });
        contentArea.appendChild(textarea);
      } else {
        editTab.classList.remove("active");
        prevTab.classList.add("active");

        const preview = document.createElement("div");
        preview.classList.add("doclib-md-preview");
        let html = this.data.md
          .replace(/^# (.*$)/gim, "<h1>$1</h1>")
          .replace(/^## (.*$)/gim, "<h2>$1</h2>")
          .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/gim, "<em>$1</em>")
          .replace(/\n$/gim, "<br />");

        preview.innerHTML = html;
        contentArea.appendChild(preview);
      }
    };

    if (!this.readOnly) {
      editTab.addEventListener("click", () => {
        isEditMode = true;
        renderUI();
      });
      prevTab.addEventListener("click", () => {
        isEditMode = false;
        renderUI();
      });
    }

    renderUI();
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
