import { API, BlockTool } from "@editorjs/editorjs";
import { IconWarning } from "@codexteam/icons";

export default class DocLibWarning implements BlockTool {
  static readonly feature = {
    id: "DocLibWarning",
    title: "DocLib Warning",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b7c81d56e715161e"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="17,17 16,5 14,8 9,17 6,20 9,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { title: string; message: string };
  private wrapper: HTMLElement | null = null;
  private _CSS: {
    block: string;
    wrapper: string;
    title: string;
    message: string;
  };

  static get toolbox() {
    return {
      title: "DocLib Warning",
      icon: IconWarning,
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      title: data.title || "",
      message: data.message || "",
    };

    this._CSS = {
      block: this.api.styles.block,
      wrapper: "cdx-warning",
      title: "DocLib Warning",
      message: "cdx-warning__message",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this._CSS.wrapper);
    this.wrapper.classList.add(this._CSS.block);

    this.wrapper.style.display = "flex";
    this.wrapper.style.alignItems = "flex-start";
    this.wrapper.style.padding = "15px";
    this.wrapper.style.backgroundColor = "rgba(230, 230, 230, 0.5)";
    this.wrapper.style.borderRadius = "3px";

    const iconWrapper = document.createElement("div");
    iconWrapper.innerHTML = IconWarning;
    iconWrapper.style.marginRight = "15px";
    iconWrapper.style.minWidth = "24px";
    iconWrapper.style.color = "#388ae5";

    const contentWrapper = document.createElement("div");
    contentWrapper.style.flexGrow = "1";

    const title = document.createElement("div");
    title.classList.add(this._CSS.title);
    title.contentEditable = "true";
    title.innerHTML = this.data.title;
    title.dataset.placeholder = "DocLib Title";
    title.style.outline = "none";
    title.style.fontWeight = "bold";
    title.style.marginBottom = "5px";

    const message = document.createElement("div");
    message.classList.add(this._CSS.message);
    message.contentEditable = "true";
    message.innerHTML = this.data.message;
    message.dataset.placeholder = "DocLib Text";
    message.style.outline = "none";

    contentWrapper.appendChild(title);
    contentWrapper.appendChild(message);

    this.wrapper.appendChild(iconWrapper);
    this.wrapper.appendChild(contentWrapper);

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const title = blockContent.querySelector(
      `.${this._CSS.title}`,
    ) as HTMLElement;
    const message = blockContent.querySelector(
      `.${this._CSS.message}`,
    ) as HTMLElement;

    return {
      title: title.innerHTML,
      message: message.innerHTML,
    };
  }

  static get sanitize() {
    return {
      title: { br: true, b: true, i: true, a: true },
      message: { br: true, b: true, i: true, a: true },
    };
  }
}
