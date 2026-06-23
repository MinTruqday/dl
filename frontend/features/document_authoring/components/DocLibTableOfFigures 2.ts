import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTableOfFigures implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Table of Figures",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-tof { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin: 16px 0; }
      .doclib-tof-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
      .doclib-tof-list { list-style: none; padding: 0; margin: 0; }
      .doclib-tof-item { margin: 8px 0; display: flex; justify-content: space-between; }
      .doclib-tof-link { color: #334155; text-decoration: none; font-size: 14px; transition: color 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .doclib-tof-link:hover { color: #2563eb; text-decoration: underline; }
      .doclib-tof-empty { font-size: 13px; color: #94a3b8; font-style: italic; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-tof");

    const title = document.createElement("div");
    title.classList.add("doclib-tof-title");
    title.innerText = "Table of Figures";
    container.appendChild(title);

    const list = document.createElement("div");
    list.classList.add("doclib-tof-list");
    container.appendChild(list);
    this.wrapper.appendChild(container);

    setTimeout(() => {
      const figures = document.querySelectorAll(".cdx-simple-image__caption, figcaption, .image-tool__caption");
      
      if (figures.length === 0) {
        const empty = document.createElement("div");
        empty.classList.add("doclib-tof-empty");
        empty.innerText = "DocLib Text";
        list.appendChild(empty);
        return;
      }

      figures.forEach((fig, index) => {
        const text = (fig as HTMLElement).innerText.trim() || `Figure ${index + 1}`;
        
        const parent = fig.closest(".ce-block") || fig.parentElement;
        if (parent && !parent.id) {
          parent.id = "figure-" + index;
        }

        const item = document.createElement("div");
        item.classList.add("doclib-tof-item");

        const link = document.createElement("a");
        link.classList.add("doclib-tof-link");
        link.href = "#" + (parent ? parent.id : "");
        link.innerText = text;
        
        link.addEventListener("click", (e) => {
          e.preventDefault();
          if (parent) parent.scrollIntoView({ behavior: "smooth", block: "center" });
        });

        item.appendChild(link);
        list.appendChild(item);
      });
    }, 500);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {};
  }
}
