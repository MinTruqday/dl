export default class DocLibIndentTune {
  static readonly feature = {
    id: "DocLibIndent",
    title: "DocLib Indent",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2f7b086539fff469"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="17,8 12,20 10,4 10,7 13,17 19,5"/></svg>',
    product: "doclib",
  } as const;

  api: any;
  data: any;
  block: any;
  wrapper: HTMLElement | null = null;

  static get isTune() {
    return true;
  }

  constructor({ api, data, config, block }: any) {
    this.api = api;
    this.data = data || { level: 0 };
    this.block = block;
  }

  render() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("ce-popover-item");
    const icon = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2f7b086539fff469"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="17,8 12,20 10,4 10,7 13,17 19,5"/></svg>`;
    wrapper.innerHTML = `<div class="ce-popover-item__icon">${icon}</div><div class="ce-popover-item__title">DocLib Indent</div>`;

    wrapper.addEventListener("click", (e) => {
      this.data.level = Math.min(10, (this.data.level || 0) + 1);
      this.applyIndent();
    });

    wrapper.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      this.data.level = Math.max(0, (this.data.level || 0) - 1);
      this.applyIndent();
    });
    wrapper.title =
      "Left click: Increase indent | Right click: Decrease indent";

    return wrapper;
  }

  wrap(blockContent: HTMLElement) {
    if (this.data && this.data.level > 0) {
      blockContent.style.marginLeft = `${this.data.level * 24}px`;
    }
    return blockContent;
  }

  applyIndent() {
    const idx = this.api.blocks.getCurrentBlockIndex();
    if (idx !== undefined && idx >= 0) {
      const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
      if (blockContent) {
        blockContent.style.marginLeft = `${(this.data.level || 0) * 24}px`;
      }
    }
  }

  save() {
    return this.data;
  }
}
