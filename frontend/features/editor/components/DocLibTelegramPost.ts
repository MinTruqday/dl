import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTelegramPost implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string };

  static get toolbox() {
    return {
      title: "DocLib Telegram",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      url: data.url || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-telegram-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-telegram-styles";
      style.innerHTML = `
            .doclib-telegram-wrapper { text-align: center; margin: 10px 0; }
            .doclib-telegram-iframe { border: none; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; min-height: 250px; background: white; }
            .doclib-telegram-input-container { display: flex; align-items: center; }
            .doclib-telegram-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-telegram-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.url) {
      const iframe = document.createElement("iframe");
      const embedUrl = this.data.url.includes("?embed=1")
        ? this.data.url
        : `${this.data.url}?embed=1`;
      iframe.src = embedUrl;
      iframe.classList.add("doclib-telegram-iframe");
      iframe.setAttribute("scrolling", "no");
      iframe.setAttribute("frameborder", "0");
      iframe.setAttribute("allowtransparency", "true");

      this.wrapper.appendChild(iframe);
    } else {
      const container = document.createElement("div");
      container.classList.add("doclib-telegram-input-container");

      const input = document.createElement("input");
      input.classList.add(this.api.styles.input, "doclib-telegram-input");
      input.placeholder = "DocLib URL";

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Embed";

      const insertPost = () => {
        if (input.value && input.value.includes("t.me/")) {
          this.data.url = input.value;
          this.buildUI();
        } else {
          input.value = "";
          input.placeholder = "DocLib URL";
        }
      };

      btn.addEventListener("click", insertPost);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") insertPost();
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
