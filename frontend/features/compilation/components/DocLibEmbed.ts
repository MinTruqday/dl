import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibEmbed implements BlockTool {
  static readonly feature = {
    id: "DocLibEmbed",
    title: "DocLib Embed",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7b175931880991ec"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="8,10 8,19 4,13 13,19 9,10 20,20"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    service: string;
    source: string;
    embed: string;
    width: number;
    height: number;
    caption: string;
  };

  static get toolbox() {
    return {
      title: "DocLib Embed",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7b175931880991ec"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="8,10 8,19 4,13 13,19 9,10 20,20"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      service: data.service || "",
      source: data.source || "",
      embed: data.embed || "",
      width: data.width || 580,
      height: data.height || 320,
      caption: data.caption || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-embed-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-embed-styles";
      style.innerHTML = `
            .doclib-embed-wrapper { text-align: center; }
            .doclib-embed-iframe { max-width: 100%; border: none; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            .doclib-embed-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 4px; }
            .doclib-embed-caption:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            .doclib-embed-input-container { display: flex; align-items: center; }
            .doclib-embed-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-embed-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.embed) {
      const iframe = document.createElement("iframe");
      iframe.src = this.data.embed;
      iframe.width = this.data.width.toString();
      iframe.height = this.data.height.toString();
      iframe.classList.add("doclib-embed-iframe");
      iframe.allowFullscreen = true;

      const caption = document.createElement("div");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.classList.add("doclib-embed-caption");

      caption.addEventListener("input", () => {
        this.data.caption = caption.innerHTML;
      });

      this.wrapper.appendChild(iframe);
      this.wrapper.appendChild(caption);
    } else {
      const container = document.createElement("div");
      container.classList.add("doclib-embed-input-container");

      const input = document.createElement("input");
      input.classList.add(this.api.styles.input, "doclib-embed-input");
      input.placeholder = "DocLib URL";

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Embed";

      const processEmbed = () => {
        const val = input.value;
        if (val.includes("youtube.com/watch?v=") || val.includes("youtu.be/")) {
          const videoId =
            val.split("v=")[1]?.split("&")[0] ||
            val.split("youtu.be/")[1]?.split("?")[0];
          if (videoId) {
            this.data.source = val;
            this.data.embed = `https://www.youtube.com/embed/${videoId}`;
            this.data.service = "youtube";
            this.buildUI();
          }
        } else {
          input.value = "";
          input.placeholder = "DocLib URL";
        }
      };

      btn.addEventListener("click", processEmbed);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") processEmbed();
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
