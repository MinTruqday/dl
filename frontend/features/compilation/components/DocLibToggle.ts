import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibToggle implements BlockTool {
  static readonly feature = {
    id: "DocLibToggle",
    title: "Toggle",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7f170dbeac285bc4"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="12,10 17,7 6,10 10,13 8,5 8,16"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { title: string; content: string; status: "open" | "closed" };

  static get toolbox() {
    return {
      title: "Toggle",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7f170dbeac285bc4"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="12,10 17,7 6,10 10,13 8,5 8,16"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      title: data.title || "",
      content: data?.content || "",
      status: data.status || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-toggle-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-toggle-styles";
      style.innerHTML = `
            .doclib-toggle-wrapper { margin: 12px 0; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; }
            .doclib-toggle-details { width: 100%; }
            .doclib-toggle-summary { padding: 12px 16px; font-weight: 600; cursor: pointer; display: flex; align-items: center; outline: none; border-bottom: 1px solid transparent; transition: border-bottom 0.2s; }
            .doclib-toggle-details[open] .doclib-toggle-summary { border-bottom: 1px solid #e2e8f0; }
            .doclib-toggle-summary::-webkit-details-marker { display: none; }
            .doclib-toggle-icon { margin-right: 8px; transition: transform 0.2s; display: flex; align-items: center; justify-content: center; }
            .doclib-toggle-details[open] .doclib-toggle-icon { transform: rotate(90deg); }
            .doclib-toggle-title { flex-grow: 1; outline: none; }
            .doclib-toggle-title:empty::before { content: 'DocLib Title'; color: #94a3b8; pointer-events: none; }
            .doclib-toggle-content { padding: 16px; min-height: 80px; outline: none; line-height: 1.6; }
            .doclib-toggle-content:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
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
    container.classList.add("doclib-toggle-wrapper");

    const details = document.createElement("details");
    details.classList.add("doclib-toggle-details");
    if (this.data.status === "open") details.open = true;

    details.addEventListener("toggle", () => {
      this.data.status = details.open ? "open" : "closed";
    });

    const summary = document.createElement("summary");
    summary.classList.add("doclib-toggle-summary");

    const icon = document.createElement("span");
    icon.classList.add("doclib-toggle-icon");
    icon.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7f170dbeac285bc4"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="12,10 17,7 6,10 10,13 8,5 8,16"/></svg>';

    const title = document.createElement("span");
    title.classList.add("doclib-toggle-title");
    title.contentEditable = "true";
    title.innerHTML = this.data.title;
    title.addEventListener("input", () => (this.data.title = title.innerHTML));

    title.addEventListener("click", (e) => e.preventDefault());

    summary.appendChild(icon);
    summary.appendChild(title);

    const content = document.createElement("div");
    content.classList.add("doclib-toggle-content");
    content.contentEditable = "true";
    content.innerHTML = this.data?.content;
    content.addEventListener(
      "input",
      () => (this.data.content = content.innerHTML),
    );

    details.appendChild(summary);
    details.appendChild(content);
    container.appendChild(details);

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
