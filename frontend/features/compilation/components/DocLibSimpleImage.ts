import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSimpleImage implements BlockTool {
  static readonly feature = {
    id: "DocLibSimpleImage",
    title: "Simple Image",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e169af2c87e56774"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,7 9,14 20,12 5,18 16,6 5,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string; caption: string };

  static get toolbox() {
    return {
      title: "Simple Image",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e169af2c87e56774"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,7 9,14 20,12 5,18 16,6 5,4"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      url: data.url || "",
      caption: data.caption || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-simple-image-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-simple-image-styles";
      style.innerHTML = `
            .doclib-simple-img-wrapper { text-align: center; }
            .doclib-simple-img { max-width: 100%; border-radius: 8px; margin-bottom: 8px; }
            .doclib-simple-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 4px; }
            .doclib-simple-caption:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            .doclib-simple-input-container { display: flex; align-items: center; }
            .doclib-simple-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-simple-img-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.url) {
      const img = document.createElement("img");
      img.src = this.data.url;
      img.classList.add("doclib-simple-img");

      const caption = document.createElement("div");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.classList.add("doclib-simple-caption");

      caption.addEventListener("input", () => {
        this.data.caption = caption.innerHTML;
      });

      this.wrapper.appendChild(img);
      this.wrapper.appendChild(caption);
    } else {
      const container = document.createElement("div");
      container.classList.add("doclib-simple-input-container");

      const input = document.createElement("input");
      input.classList.add(this.api.styles.input, "doclib-simple-input");
      input.placeholder = "DocLib URL";

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Insert";

      const insertImg = () => {
        if (input.value) {
          this.data.url = input.value;
          this.buildUI();
        }
      };

      btn.addEventListener("click", insertImg);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") insertImg();
      });

      container.appendChild(input);
      container.appendChild(btn);
      this.wrapper.appendChild(container);
    }
  }

  save() {
    return this.data;
  }
}
