import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibNestedList implements BlockTool {
  static readonly feature = {
    id: "DocLibNestedList",
    title: "DocLib Nested List",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1505862bd4202408"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,9 19,13 12,19 6,12 14,17 5,12"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    style: "ordered" | "unordered";
    items: { content: string; items: any[] }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Nested List",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1505862bd4202408"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="8,9 19,13 12,19 6,12 14,17 5,12"/></svg>',
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
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      style: data.style || "",
      items: data.items && data.items.length > 0 ? data.items : [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-nested-list-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-nested-list-styles";
      style.innerHTML = `
            .doclib-nl-wrapper { margin: 8px 0; padding-left: 24px; outline: none; }
            .doclib-nl-item { margin: 4px 0; line-height: 1.6; }
            .doclib-nl-content { outline: none; display: inline-block; min-width: 50px; }
            .doclib-nl-content:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            ul.doclib-nl-wrapper { list-style-type: disc; }
            ol.doclib-nl-wrapper { list-style-type: decimal; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.appendChild(this.renderList(this.data.items, this.data.style));
    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");
    const styles = [
      { name: "unordered", icon: "•" },
      { name: "ordered", icon: "1." },
    ];

    styles.forEach((s) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      if (this.data.style === s.name)
        btn.classList.add(this.api.styles.settingsButtonActive);
      btn.innerHTML = s.icon;
      btn.addEventListener("click", () => {
        this.data.style = s.name as any;
        this.wrapper!.innerHTML = "";
        this.wrapper!.appendChild(
          this.renderList(this.data.items, this.data.style),
        );
      });
      wrapper.appendChild(btn);
    });
    return wrapper;
  }

  private renderList(items: any[], style: string) {
    const list = document.createElement(style === "ordered" ? "ol" : "ul");
    list.classList.add("doclib-nl-wrapper");

    items.forEach((item, index) => {
      const li = document.createElement("li");
      li.classList.add("doclib-nl-item");

      const content = document.createElement("div");
      content.classList.add("doclib-nl-content");
      content.contentEditable = !this.readOnly ? "true" : "false";
      content.innerHTML = item.content;

      content.addEventListener("input", () => {
        item.content = content.innerHTML;
      });

      content.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          items.splice(index + 1, 0, { content: "", items: [] });
          this.wrapper!.innerHTML = "";
          this.wrapper!.appendChild(
            this.renderList(this.data.items, this.data.style),
          );
        } else if (e.key === "Tab") {
          e.preventDefault();
          if (!e.shiftKey && index > 0) {
            const prevItem = items[index - 1];
            prevItem.items.push(items.splice(index, 1)[0]);
            this.wrapper!.innerHTML = "";
            this.wrapper!.appendChild(
              this.renderList(this.data.items, this.data.style),
            );
          }
        }
      });

      li.appendChild(content);
      if (item.items && item.items.length > 0) {
        li.appendChild(this.renderList(item.items, style));
      }
      list.appendChild(li);
    });

    return list;
  }

  save() {
    return this.data;
  }
}
