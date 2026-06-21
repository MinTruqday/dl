import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibNewsTicker implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib News Ticker",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      text: data?.text || "",
      speed: data?.speed || 15,
      bg: data?.bg || "#ef4444",
      color: data?.color || "#ffffff",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-nt { display: flex; background: var(--nt-bg); color: var(--nt-col); padding: 8px 16px; border-radius: 4px; overflow: hidden; font-family: sans-serif; align-items: center; margin: 16px 0; }
      .doclib-nt-label { font-weight: bold; text-transform: uppercase; padding-right: 16px; border-right: 2px solid rgba(255,255,255,0.3); z-index: 2; white-space: nowrap; }
      .doclib-nt-track { flex: 1; overflow: hidden; padding-left: 16px; position: relative; height: 20px; }
      .doclib-nt-marquee { white-space: nowrap; position: absolute; animation: doclib-marquee var(--nt-speed) linear infinite; }
      @keyframes doclib-marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
      .doclib-nt-input { width: 100%; padding: 8px; margin-bottom: 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; }
    `;
    this.wrapper.appendChild(style);

    if (!this.readOnly) {
      const input = document.createElement("input");
      input.classList.add("doclib-nt-input");
      input.placeholder = "DocLib News Ticker Text";
      input.value = this.data.text;
      input.addEventListener("input", () => {
        this.data.text = input.value;
        this.buildUI();
      });
      this.wrapper.appendChild(input);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    let container = this.wrapper.querySelector(".doclib-nt") as HTMLElement;
    if (!container) {
      container = document.createElement("div");
      container.classList.add("doclib-nt");
      this.wrapper.appendChild(container);
    } else {
      container.innerHTML = "";
    }

    container.style.setProperty("--nt-bg", this.data.bg);
    container.style.setProperty("--nt-col", this.data.color);
    container.style.setProperty("--nt-speed", `${this.data.speed}s`);

    const label = document.createElement("div");
    label.classList.add("doclib-nt-label");
    label.innerText = "BREAKING";
    container.appendChild(label);

    const track = document.createElement("div");
    track.classList.add("doclib-nt-track");

    const marquee = document.createElement("div");
    marquee.classList.add("doclib-nt-marquee");
    marquee.innerText = this.data.text || "DocLib Breaking News...";
    track.appendChild(marquee);

    container.appendChild(track);
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
