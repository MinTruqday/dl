export default class DocLibIndentTune {
  api: any;
  data: any;
  block: any;
  wrapper: HTMLElement | null = null;
  
  static get isTune() { return true; }
  
  constructor({ api, data, config, block }: any) {
    this.api = api;
    this.data = data || { level: 0 };
    this.block = block;
  }

  render() {
    const wrapper = document.createElement('div');
    wrapper.classList.add('ce-popover-item');
    const icon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="12" x2="11" y2="12"></line><line x1="21" y1="6" x2="11" y2="6"></line><line x1="21" y1="18" x2="11" y2="18"></line><polyline points="8 8 12 12 8 16"></polyline></svg>`;
    wrapper.innerHTML = `<div class="ce-popover-item__icon">${icon}</div><div class="ce-popover-item__title">DocLib Indent</div>`;
    
    wrapper.addEventListener('click', (e) => {
      this.data.level = Math.min(10, (this.data.level || 0) + 1);
      this.applyIndent();
    });
    
    wrapper.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.data.level = Math.max(0, (this.data.level || 0) - 1);
      this.applyIndent();
    });
    wrapper.title = "Left click: Increase indent | Right click: Decrease indent";

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
