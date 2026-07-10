import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibBalloons implements BlockTune {
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
    btn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 11.5C21 16.1944 16.9706 20 12 20C10.7493 20 9.55831 19.7423 8.47779 19.2789L4.5 20.5L5.75338 16.6575C4.65486 15.2536 4 13.4542 4 11.5C4 6.80558 7.58172 3 12 3C16.4183 3 21 6.80558 21 11.5Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>`;
    btn.dataset.title = "DocLib Balloons";

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
      w.classList.add("doclib-doclibballoons-active");
    }
    w.appendChild(blockContent);
    return w;
  }
}
