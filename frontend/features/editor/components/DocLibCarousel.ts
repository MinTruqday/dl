import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCarousel implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { urls: string[] };
  private currentIndex: number = 0;

  static get toolbox() {
    return {
      title: "DocLib Carousel",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { urls: Array.isArray(data.urls) ? data.urls : [] };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-carousel-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-carousel-styles";
      style.innerHTML = `
            .doclib-carousel-wrapper { position: relative; width: 100%; aspect-ratio: 16/9; border-radius: 8px; overflow: hidden; background: #f1f5f9; margin: 12px 0; border: 1px solid #e2e8f0; }
            .doclib-carousel-img { width: 100%; height: 100%; object-fit: cover; }
            .doclib-carousel-btn { position: absolute; top: 50%; transform: translateY(-50%); background: rgba(0,0,0,0.5); color: white; border: none; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 10; opacity: 0; transition: opacity 0.2s; font-size: 20px; padding-bottom: 3px; }
            .doclib-carousel-wrapper:hover .doclib-carousel-btn { opacity: 1; }
            .doclib-carousel-prev { left: 8px; }
            .doclib-carousel-next { right: 8px; }
            .doclib-carousel-dots { position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); display: flex; gap: 4px; z-index: 10; }
            .doclib-carousel-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.5); cursor: pointer; transition: background 0.2s; }
            .doclib-carousel-dot.active { background: white; }
            .doclib-carousel-edit-overlay { position: absolute; top: 8px; right: 8px; z-index: 10; display: flex; gap: 8px; opacity: 0; transition: opacity 0.2s; }
            .doclib-carousel-wrapper:hover .doclib-carousel-edit-overlay { opacity: 1; }
            .doclib-carousel-edit-btn { padding: 4px 8px; font-size: 12px; background: rgba(0,0,0,0.6); color: white; border: none; border-radius: 4px; cursor: pointer; }
            .doclib-carousel-edit-btn:hover { background: rgba(0,0,0,0.8); }
            .doclib-carousel-input-container { padding: 16px; display: flex; gap: 8px; align-items: center; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.urls.length > 0) {
      const container = document.createElement("div");
      container.classList.add("doclib-carousel-wrapper");

      const img = document.createElement("img");
      img.classList.add("doclib-carousel-img");
      img.src = this.data.urls[this.currentIndex];
      container.appendChild(img);

      if (this.data.urls.length > 1) {
        const prev = document.createElement("button");
        prev.classList.add("doclib-carousel-btn", "doclib-carousel-prev");
        prev.innerHTML = "&lsaquo;";
        prev.addEventListener("click", () => {
          this.currentIndex =
            (this.currentIndex - 1 + this.data.urls.length) %
            this.data.urls.length;
          img.src = this.data.urls[this.currentIndex];
          updateDots();
        });

        const next = document.createElement("button");
        next.classList.add("doclib-carousel-btn", "doclib-carousel-next");
        next.innerHTML = "&rsaquo;";
        next.addEventListener("click", () => {
          this.currentIndex = (this.currentIndex + 1) % this.data.urls.length;
          img.src = this.data.urls[this.currentIndex];
          updateDots();
        });

        const dots = document.createElement("div");
        dots.classList.add("doclib-carousel-dots");
        const dotElements = this.data.urls.map((_, i) => {
          const dot = document.createElement("div");
          dot.classList.add("doclib-carousel-dot");
          if (i === this.currentIndex) dot.classList.add("active");
          dot.addEventListener("click", () => {
            this.currentIndex = i;
            img.src = this.data.urls[this.currentIndex];
            updateDots();
          });
          dots.appendChild(dot);
          return dot;
        });

        const updateDots = () => {
          dotElements.forEach((d, i) =>
            d.classList.toggle("active", i === this.currentIndex),
          );
        };

        container.appendChild(prev);
        container.appendChild(next);
        container.appendChild(dots);
      }

      const overlay = document.createElement("div");
      overlay.classList.add("doclib-carousel-edit-overlay");

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-carousel-edit-btn");
      addBtn.innerText = "+ Add Image";
      addBtn.addEventListener("click", () => {
        const url = prompt("Enter new image URL:");
        if (url) {
          this.data.urls.push(url);
          this.currentIndex = this.data.urls.length - 1;
          this.buildUI();
        }
      });

      const rmBtn = document.createElement("button");
      rmBtn.classList.add("doclib-carousel-edit-btn");
      rmBtn.innerText = "- Delete Image";
      rmBtn.addEventListener("click", () => {
        if (confirm("Delete image from Carousel?")) {
          this.data.urls.splice(this.currentIndex, 1);
          this.currentIndex = Math.max(0, this.currentIndex - 1);
          this.buildUI();
        }
      });

      overlay.appendChild(addBtn);
      overlay.appendChild(rmBtn);
      container.appendChild(overlay);

      this.wrapper.appendChild(container);
    } else {
      const container = document.createElement("div");
      container.classList.add("doclib-carousel-input-container");

      const input = document.createElement("input");
      input.classList.add(this.api.styles.input);
      input.style.flexGrow = "1";
      input.placeholder = "Enter first image URL";

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Create Carousel";

      const insert = () => {
        if (input.value) {
          this.data.urls = [input.value];
          this.buildUI();
        }
      };

      btn.addEventListener("click", insert);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") insert();
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
