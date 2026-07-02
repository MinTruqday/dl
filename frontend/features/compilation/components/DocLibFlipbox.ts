import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFlipbox implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { front: string; back: string; bgColor: string };

  static get toolbox() {
    return {
      title: "DocLib Flipbox",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      front: data.front || "",
      back: data.back || "",
      bgColor: data.bgColor || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-flipbox-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-flipbox-styles";
      style.innerHTML = `
            .doclib-fb-wrapper { perspective: 1000px; width: 100%; height: 200px; margin: 16px 0; }
            .doclib-fb-inner { position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.6s; transform-style: preserve-3d; }
            .doclib-fb-wrapper:hover .doclib-fb-inner { transform: rotateY(180deg); }
            .doclib-fb-front, .doclib-fb-back { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 12px; display: flex; align-items: center; justify-content: center; padding: 24px; font-size: 1.2em; font-weight: 600; color: white; outline: none; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .doclib-fb-back { transform: rotateY(180deg); background-color: #0f172a !important; }
            .doclib-fb-front:empty::before { content: 'Enter front content'; opacity: 0.7; }
            .doclib-fb-back:empty::before { content: 'Enter back content'; opacity: 0.7; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");
    wrapper.style.display = "flex";
    wrapper.style.gap = "8px";
    wrapper.style.padding = "8px";

    const colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];
    colors.forEach((c) => {
      const btn = document.createElement("div");
      btn.style.width = "24px";
      btn.style.height = "24px";
      btn.style.borderRadius = "50%";
      btn.style.backgroundColor = c;
      btn.style.cursor = "pointer";
      if (c === this.data.bgColor) btn.style.border = "2px solid #0f172a";
      btn.addEventListener("click", () => {
        this.data.bgColor = c;
        this.buildUI();
      });
      wrapper.appendChild(btn);
    });
    return wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-fb-wrapper");

    const inner = document.createElement("div");
    inner.classList.add("doclib-fb-inner");

    const front = document.createElement("div");
    front.classList.add("doclib-fb-front");
    front.style.backgroundColor = this.data.bgColor;
    front.contentEditable = "true";
    front.innerHTML = this.data.front;
    front.addEventListener("input", () => (this.data.front = front.innerHTML));

    const back = document.createElement("div");
    back.classList.add("doclib-fb-back");
    back.contentEditable = "true";
    back.innerHTML = this.data.back;
    back.addEventListener("input", () => (this.data.back = back.innerHTML));

    inner.appendChild(front);
    inner.appendChild(back);
    container.appendChild(inner);

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
