import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibAnchor implements BlockTune {
  static readonly feature = {
    id: "DocLibAnchor",
    title: "DocLib Anchor",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9ddd899a066a4693"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="8,4 5,5 10,8 6,15 12,20 10,20"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private _data: string;
  private block: any;
  private maxWords = 5;

  static get isTune() {
    return true;
  }

  constructor({ api, data, block }: { api: API; data: any; block: any }) {
    this.api = api;
    this.block = block;
    this._data = typeof data === "string" ? data : data?.anchor || "";
  }

  get currentAnchor() {
    if (this._data.length > 0) {
      const anchorText = this._data
        .replace(/[^a-zA-Z0-9-_ ]/g, "")
        .replace(/-/g, "_");
      const words = anchorText.split(/\s+/);
      return words.slice(0, this.maxWords).join("_");
    }
    return undefined;
  }

  render() {
    const toggler = document.createElement("div");
    toggler.classList.add(this.api.styles.settingsButton);
    toggler.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="9ddd899a066a4693"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="8,4 5,5 10,8 6,15 12,20 10,20"/></svg>';

    if (this.currentAnchor) {
      toggler.classList.add(this.api.styles.settingsButtonActive);
    }

    this.api.tooltip.onHover(toggler, "Anchor", {
      placement: "top",
      hidingDelay: 500,
    });

    toggler.addEventListener("click", () => {
      if (this.currentAnchor) {
        this._data = "";
        toggler.classList.remove(this.api.styles.settingsButtonActive);
      } else {
        const blockContent = this.block.holder.innerText;
        this._data =
          blockContent || `block_${Math.floor(Math.random() * 1000)}`;
        toggler.classList.add(this.api.styles.settingsButtonActive);
      }

      this.block.dispatchChange();
    });

    return toggler;
  }

  save() {
    return this.currentAnchor || "";
  }
}
