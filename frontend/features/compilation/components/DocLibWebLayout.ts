import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibWebLayout implements BlockTune {
  static get isTune() {
    return true;
  }

  private api: API;
  private data: any;
  private wrapper: HTMLElement;

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = data || { enabled: false };
    this.wrapper = document.createElement("div");
  }

  render() {
    const btn = document.createElement("button");
    btn.classList.add(this.api.styles.settingsButton);
    btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V18C21 19.1046 20.1046 20 19 20H5C3.89543 20 3 19.1046 3 18V6Z" stroke="currentColor" stroke-width="2"/><path d="M3 8H21" stroke="currentColor" stroke-width="2"/></svg>`;
    btn.dataset.title = "DocLib Web Layout";

    if (this.data.enabled) {
      btn.classList.add(this.api.styles.settingsButtonActive);
    }

    btn.addEventListener("click", () => {
      this.data.enabled = !this.data.enabled;
      btn.classList.toggle(this.api.styles.settingsButtonActive);
    });

    this.wrapper.appendChild(btn);
    return this.wrapper;
  }

  save() {
    return this.data;
  }

  wrap(blockContent: HTMLElement) {
    const w = document.createElement("div");
    if (this.data.enabled) {
      w.classList.add("doclib-doclibweblayout-active");
    }
    w.appendChild(blockContent);
    return w;
  }
}
