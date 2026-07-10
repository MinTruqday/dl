import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibReadMode implements BlockTune {
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
    btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 19.5V4.5C4 4.5 7 3 12 5V20.5C7 18.5 4 19.5 4 19.5ZM12 5C17 3 20 4.5 20 4.5V19.5C20 19.5 17 18.5 12 20.5V5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    btn.dataset.title = "DocLib Read Mode";

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
      w.classList.add("doclib-doclibreadmode-active");
    }
    w.appendChild(blockContent);
    return w;
  }
}
