import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCrossReference implements BlockTool {
  static readonly feature = {
    id: "DocLibCrossReference",
    title: "DocLib CrossReference",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ab29ca4f78ca710a"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,11 19,15 5,19 15,14 16,17 7,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Cross Reference",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ab29ca4f78ca710a"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,11 19,15 5,19 15,14 16,17 7,14"/></svg>',
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
      text: data?.text || "",
      targetId: data?.targetId || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-xref { display: inline-flex; align-items: center; gap: 4px; padding: 2px 6px; background: hsl(var(--surface-quiet)); border-radius: 4px; cursor: pointer; color: hsl(var(--brand)); font-weight: 500; font-size: 14px; text-decoration: none; transition: background 0.2s; }
      .doclib-xref:hover { background: hsl(var(--border)); text-decoration: underline; }
      .doclib-xref-edit { display: flex; gap: 8px; background: hsl(var(--surface)); border: 1px solid hsl(var(--border)); padding: 12px; border-radius: 6px; }
      .doclib-xref-input { flex: 1; padding: 8px; border: 1px solid hsl(var(--border)); border-radius: 4px; outline: none; font-size: 14px; }
    `;
    this.wrapper.appendChild(style);

    if (this.readOnly) {
      const link = document.createElement("a");
      link.classList.add("doclib-xref");
      link.innerText = this.data.text || "DocLib Text";
      link.href = "#" + this.data.targetId;
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = document.getElementById(this.data.targetId);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "center" });
          target.style.transition = "background 0.5s";
          target.style.background = "hsl(var(--warning-soft))";
          setTimeout(() => {
            target.style.background = "transparent";
          }, 1500);
        }
      });
      this.wrapper.appendChild(link);
      return this.wrapper;
    }

    const edit = document.createElement("div");
    edit.classList.add("doclib-xref-edit");

    const textInput = document.createElement("input");
    textInput.classList.add("doclib-xref-input");
    textInput.placeholder = "DocLib Text";
    textInput.value = this.data.text;
    textInput.addEventListener("input", () => {
      this.data.text = textInput.value;
    });

    const targetInput = document.createElement("input");
    targetInput.classList.add("doclib-xref-input");
    targetInput.placeholder = "DocLib Input";
    targetInput.value = this.data.targetId;
    targetInput.addEventListener("input", () => {
      this.data.targetId = targetInput.value;
    });

    edit.appendChild(textInput);
    edit.appendChild(targetInput);
    this.wrapper.appendChild(edit);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      targetId: this.data.targetId,
    };
  }
}
