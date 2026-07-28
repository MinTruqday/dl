import { API, BlockTool } from "@editorjs/editorjs";
import { IconQuote } from "@codexteam/icons";

export default class DocLibQuote implements BlockTool {
  static readonly feature = {
    id: "DocLibQuote",
    title: "DocLib Quote",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c0a06b2f5667d364"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="9,11 9,17 5,5 11,19 19,19 18,18"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { text: string; caption: string; alignment: string };
  private wrapper: HTMLElement | null = null;
  private _CSS: {
    block: string;
    wrapper: string;
    text: string;
    caption: string;
  };

  static get toolbox() {
    return {
      title: "DocLib Quote",
      icon: IconQuote,
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }

  constructor({ api, data, config }: { api: API; data: any; config: any }) {
    this.api = api;
    this.data = {
      text: data.text || "",
      caption: data.caption || "",
      alignment: data.alignment || config?.defaultAlignment || "",
    };

    this._CSS = {
      block: this.api.styles.block,
      wrapper: "cdx-quote",
      text: "cdx-quote__text",
      caption: "cdx-quote__caption",
    };
  }

  render() {
    this.wrapper = document.createElement("blockquote");
    this.wrapper.classList.add(this._CSS.wrapper);
    this.wrapper.classList.add(this._CSS.block);
    this.wrapper.style.textAlign = this.data.alignment;

    this.wrapper.style.margin = "20px 0";
    this.wrapper.style.padding = "10px 20px";
    this.wrapper.style.borderLeft = "3px solid #000";
    this.wrapper.style.backgroundColor = "rgba(0,0,0,0.02)";
    this.wrapper.style.fontStyle = "italic";

    const text = document.createElement("div");
    text.classList.add(this._CSS.text);
    text.contentEditable = "true";
    text.innerHTML = this.data.text;
    text.dataset.placeholder = "DocLib Text";
    text.style.outline = "none";

    const caption = document.createElement("div");
    caption.classList.add(this._CSS.caption);
    caption.contentEditable = "true";
    caption.innerHTML = this.data.caption;
    caption.dataset.placeholder = "DocLib Input";
    caption.style.outline = "none";
    caption.style.marginTop = "10px";
    caption.style.fontSize = "14px";
    caption.style.fontWeight = "bold";
    caption.style.fontStyle = "normal";
    caption.style.color = "#7e838b";

    this.wrapper.appendChild(text);
    this.wrapper.appendChild(caption);

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const text = blockContent.querySelector(
      `.${this._CSS.text}`,
    ) as HTMLElement;
    const caption = blockContent.querySelector(
      `.${this._CSS.caption}`,
    ) as HTMLElement;

    return {
      text: text.innerHTML,
      caption: caption.innerHTML,
      alignment: this.data.alignment,
    };
  }

  static get sanitize() {
    return {
      text: { br: true, b: true, i: true, a: true },
      caption: { br: true, b: true, i: true, a: true },
      alignment: {},
    };
  }
}
