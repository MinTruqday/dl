import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTableOfContents implements BlockTool {
  static readonly feature = {
    id: "DocLibTableOfContents",
    title: "Table Of Contents",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1868a65ff5a86705"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="11,6 17,14 11,19 5,9 10,12 11,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Table Of Contents",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1868a65ff5a86705"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="11,6 17,14 11,19 5,9 10,12 11,14"/></svg>',
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
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-toc {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        margin: 16px 0;
      }
      .doclib-toc-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 16px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .doclib-toc-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .doclib-toc-item {
        margin: 8px 0;
      }
      .doclib-toc-link {
        color: #334155;
        text-decoration: none;
        font-size: 14px;
        transition: color 0.2s;
      }
      .doclib-toc-link:hover {
        color: #2563eb;
      }
      .doclib-toc-level-1 { margin-left: 0; font-weight: 600; }
      .doclib-toc-level-2 { margin-left: 16px; }
      .doclib-toc-level-3 { margin-left: 32px; font-size: 13px; color: #64748b; }
      .doclib-toc-empty {
        font-size: 13px;
        color: #94a3b8;
        font-style: italic;
      }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-toc");

    const title = document.createElement("div");
    title.classList.add("doclib-toc-title");
    title.innerText = "Table of Contents";
    container.appendChild(title);

    const list = document.createElement("div");
    list.classList.add("doclib-toc-list");
    container.appendChild(list);
    this.wrapper.appendChild(container);

    setTimeout(() => {
      const headers = document.querySelectorAll(
        "h1, h2, h3, h4, h5, h6, .ce-header",
      );

      if (headers.length === 0) {
        const empty = document.createElement("div");
        empty.classList.add("doclib-toc-empty");
        empty.innerText = "No headings found in the document";
        list.appendChild(empty);
        return;
      }

      headers.forEach((h, index) => {
        let level = 1;
        if (h.tagName.toLowerCase().startsWith("h")) {
          level = parseInt(h.tagName.substring(1), 10);
        } else if (h.classList.contains("ce-header")) {
          const hTag = h.querySelector("h1, h2, h3, h4, h5, h6");
          if (hTag) level = parseInt(hTag.tagName.substring(1), 10);
        }

        const text = (h as HTMLElement).innerText.trim();
        if (!text) return;

        if (!h.id) {
          h.id = "heading-" + index;
        }

        const item = document.createElement("div");
        item.classList.add("doclib-toc-item", `doclib-toc-level-${level}`);

        const link = document.createElement("a");
        link.classList.add("doclib-toc-link");
        link.href = "#" + h.id;
        link.innerText = text;

        link.addEventListener("click", (e) => {
          e.preventDefault();
          h.scrollIntoView({ behavior: "smooth", block: "start" });
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
