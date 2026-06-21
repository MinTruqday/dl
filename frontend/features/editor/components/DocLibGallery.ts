import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibGallery implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { urls: string[] };

  static get toolbox() {
    return {
      title: "DocLib Gallery",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      urls: Array.isArray(data.urls) ? data.urls : [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-gallery-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-gallery-styles";
      style.innerHTML = `
            .doclib-gallery-wrapper { margin: 10px 0; }
            .doclib-gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-bottom: 10px; }
            .doclib-gallery-item { position: relative; width: 100%; padding-top: 100%; border-radius: 8px; overflow: hidden; background: #f1f5f9; }
            .doclib-gallery-item img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
            .doclib-gallery-item .remove-btn { position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,0.5); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; justify-content: center; align-items: center; opacity: 0; transition: opacity 0.2s; }
            .doclib-gallery-item:hover .remove-btn { opacity: 1; }
            .doclib-gallery-input-container { display: flex; align-items: center; }
            .doclib-gallery-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-gallery-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.urls.length > 0) {
      const grid = document.createElement("div");
      grid.classList.add("doclib-gallery-grid");

      this.data.urls.forEach((url, index) => {
        const item = document.createElement("div");
        item.classList.add("doclib-gallery-item");

        const img = document.createElement("img");
        img.src = url;

        const btn = document.createElement("button");
        btn.classList.add("remove-btn");
        btn.innerHTML = "&times;";
        btn.addEventListener("click", () => {
          this.data.urls.splice(index, 1);
          this.buildUI();
        });

        item.appendChild(img);
        item.appendChild(btn);
        grid.appendChild(item);
      });
      this.wrapper.appendChild(grid);
    }

    const container = document.createElement("div");
    container.classList.add("doclib-gallery-input-container");

    const input = document.createElement("input");
    input.classList.add(this.api.styles.input, "doclib-gallery-input");
    input.placeholder = "DocLib URL";

    const btn = document.createElement("button");
    btn.classList.add(this.api.styles.button);
    btn.innerText = "Add Image";

    const insertImg = () => {
      if (input.value) {
        this.data.urls.push(input.value);
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

  save() {
    return this.data;
  }
}
