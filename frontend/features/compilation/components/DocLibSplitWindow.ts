import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibSplitWindow implements BlockTune {
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
    btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="2"/><path d="M4 12H20" stroke="currentColor" stroke-width="2"/></svg>`;
    btn.dataset.title = "DocLib Split Window";

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
      w.classList.add("doclib-doclibsplitwindow-active");
    }
    w.appendChild(blockContent);
    return w;
  }
}
