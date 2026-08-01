import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibHeader implements BlockTool {
  static readonly feature = {
    id: "DocLibHeader",
    title: "DocLib Header",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e32a0b93159f3252"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="10,12 15,15 8,10 20,18 15,17 15,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string; level: number };

  static get toolbox() {
    return {
      title: "DocLib Header",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e32a0b93159f3252"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="10,12 15,15 8,10 20,18 15,17 15,14"/></svg>',
    };
  }
  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return false;
  }
  static get sanitize() {
    return { text: { br: true, b: true, i: true, a: true, span: true } };
  }
  static get conversionConfig() {
    return { export: "text", import: "text" };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { text: data.text || "", level: data.level || 2 };
  }

  render() {
    this.wrapper = document.createElement(`h${this.data.level}`);
    this.wrapper.classList.add(this.api.styles.block, "doclib-header");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.text;
    this.wrapper.dataset.placeholder = `Heading ${this.data.level}`;

    if (!document.getElementById("doclib-header-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-header-styles";
      style.innerHTML = `
            .doclib-header { outline: none; margin: 16px 0 8px 0; font-weight: 700; line-height: 1.3; }
            h1.doclib-header { font-size: 2.25em; }
            h2.doclib-header { font-size: 1.75em; }
            h3.doclib-header { font-size: 1.5em; }
            h4.doclib-header { font-size: 1.25em; }
            h5.doclib-header { font-size: 1.1em; }
            h6.doclib-header { font-size: 1em; }
            .doclib-header[data-placeholder]:empty::before { content: attr(data-placeholder); color: hsl(var(--ink-faint)); pointer-events: none; font-weight: normal; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.addEventListener("input", () => {
      this.data.text = this.wrapper!.innerHTML;
    });
    this.wrapper.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.api.blocks.insert();
        this.api.caret.setToBlock(this.api.blocks.getCurrentBlockIndex() + 1);
      }
    });

    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");
    [1, 2, 3, 4, 5, 6].forEach((level) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      if (this.data.level === level)
        btn.classList.add(this.api.styles.settingsButtonActive);
      btn.innerHTML = `H${level}`;
      btn.addEventListener("click", () => {
        this.data.level = level;
        if (this.wrapper) {
          const newWrapper = document.createElement(`h${level}`);
          newWrapper.classList.add(this.api.styles.block, "doclib-header");
          newWrapper.contentEditable = "true";
          newWrapper.innerHTML = this.wrapper.innerHTML;
          newWrapper.dataset.placeholder = `Heading ${level}`;
          newWrapper.addEventListener("input", () => {
            this.data.text = newWrapper.innerHTML;
          });
          newWrapper.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              this.api.blocks.insert();
              this.api.caret.setToBlock(
                this.api.blocks.getCurrentBlockIndex() + 1,
              );
            }
          });
          this.wrapper.replaceWith(newWrapper);
          this.wrapper = newWrapper;
        }

        Array.from(wrapper.children).forEach((c) =>
          c.classList.remove(this.api.styles.settingsButtonActive),
        );
        btn.classList.add(this.api.styles.settingsButtonActive);
      });
      wrapper.appendChild(btn);
    });
    return wrapper;
  }

  save(blockContent: HTMLElement) {
    return { text: blockContent.innerHTML, level: this.data.level };
  }
}
