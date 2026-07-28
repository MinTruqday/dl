import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibNestedChecklist implements BlockTool {
  static readonly feature = {
    id: "DocLibNestedChecklist",
    title: "DocLib NestedChecklist",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7fd01601be5a94d0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,8 9,5 7,9 16,8 7,15 7,14"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { items: { text: string; checked: boolean; depth: number }[] };

  static get toolbox() {
    return {
      title: "DocLib Checklist",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7fd01601be5a94d0"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,8 9,5 7,9 16,8 7,15 7,14"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      items: data.items && data.items.length > 0 ? data.items : [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-nested-checklist-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-nested-checklist-styles";
      style.innerHTML = `
            .doclib-ncl-wrapper { margin: 8px 0; }
            .doclib-ncl-item { display: flex; align-items: flex-start; gap: 8px; margin: 4px 0; }
            .doclib-ncl-checkbox { width: 18px; height: 18px; cursor: pointer; accent-color: #3b82f6; margin-top: 4px; }
            .doclib-ncl-text { flex-grow: 1; outline: none; line-height: 1.6; padding: 2px 0; }
            .doclib-ncl-text:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            .doclib-ncl-item.checked .doclib-ncl-text { text-decoration: line-through; color: #94a3b8; }
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
    container.classList.add("doclib-ncl-wrapper");

    this.data.items.forEach((item, index) => {
      const itemDiv = document.createElement("div");
      itemDiv.classList.add("doclib-ncl-item");
      itemDiv.style.marginLeft = `${item.depth * 24}px`;
      if (item.checked) itemDiv.classList.add("checked");

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = item.checked;
      checkbox.classList.add("doclib-ncl-checkbox");
      checkbox.addEventListener("change", () => {
        item.checked = checkbox.checked;
        itemDiv.classList.toggle("checked", item.checked);
      });

      const text = document.createElement("div");
      text.classList.add("doclib-ncl-text");
      text.contentEditable = "true";
      text.innerHTML = item.text;
      text.addEventListener("input", () => (item.text = text.innerHTML));

      text.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
          e.preventDefault();
          if (e.shiftKey) {
            item.depth = Math.max(0, item.depth - 1);
          } else {
            item.depth = Math.min(4, item.depth + 1);
          }
          itemDiv.style.marginLeft = `${item.depth * 24}px`;
        } else if (e.key === "Enter") {
          e.preventDefault();
          this.data.items.splice(index + 1, 0, {
            text: "",
            checked: false,
            depth: item.depth,
          });
          this.buildUI();

          setTimeout(() => {
            const newText = container.children[index + 1].querySelector(
              ".doclib-ncl-text",
            ) as HTMLElement;
            if (newText) newText.focus();
          }, 0);
        } else if (e.key === "Backspace" && item.text === "") {
          e.preventDefault();
          if (item.depth > 0) {
            item.depth--;
            itemDiv.style.marginLeft = `${item.depth * 24}px`;
          } else if (this.data.items.length > 1) {
            this.data.items.splice(index, 1);
            this.buildUI();
            setTimeout(() => {
              const prevText = container.children[
                Math.max(0, index - 1)
              ].querySelector(".doclib-ncl-text") as HTMLElement;
              if (prevText) prevText.focus();
            }, 0);
          }
        }
      });

      itemDiv.appendChild(checkbox);
      itemDiv.appendChild(text);
      container.appendChild(itemDiv);
    });

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
