import { API, BlockTool } from "@editorjs/editorjs";
import { IconDelimiter } from "@codexteam/icons";

export default class DocLibDelimiter implements BlockTool {
  static readonly feature = {
    id: "DocLibDelimiter",
    title: "Đường phân cách",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="bce14d750fe60686"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="5,8 13,19 19,13 10,19 19,10 6,17"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: any;
  private wrapper: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "Đường phân cách",
      icon: IconDelimiter,
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const asterisks = document.createElement("div");
    asterisks.classList.add("ce-delimiter");
    asterisks.style.lineHeight = "1.6em";
    asterisks.style.width = "100%";
    asterisks.style.textAlign = "center";
    asterisks.style.color = "#7e838b";
    asterisks.style.fontSize = "30px";
    asterisks.style.letterSpacing = "0.2em";
    asterisks.innerHTML = "***";

    this.wrapper.appendChild(asterisks);
    return this.wrapper;
  }

  save() {
    return {};
  }
}
