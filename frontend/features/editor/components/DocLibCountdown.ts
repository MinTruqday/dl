import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCountdown implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { title: string; targetDate: string };
  private readOnly: boolean;
  private timerId: any = null;

  static get toolbox() {
    return {
      title: "DocLib Countdown",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      title: data.title || "",
      targetDate:
        data.targetDate || new Date(Date.now() + 86400000 * 7).toISOString(),
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-countdown-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-countdown-styles";
      style.innerHTML = `
            .doclib-cd-wrapper { margin: 16px 0; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 24px; color: white; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
            .doclib-cd-title { font-size: 1.2em; font-weight: 600; margin-bottom: 16px; outline: none; color: #e2e8f0; }
            .doclib-cd-grid { display: flex; justify-content: center; gap: 16px; }
            .doclib-cd-box { background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 8px; min-width: 80px; backdrop-filter: blur(4px); }
            .doclib-cd-num { font-size: 2.5em; font-weight: 700; line-height: 1; margin-bottom: 4px; font-variant-numeric: tabular-nums; }
            .doclib-cd-label { font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600; }
            .doclib-cd-edit { margin-top: 16px; text-align: center; }
            .doclib-cd-input { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 6px 12px; border-radius: 4px; outline: none; }
            .doclib-cd-input::-webkit-calendar-picker-indicator { filter: invert(1); }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-cd-wrapper");

    const title = document.createElement("div");
    title.classList.add("doclib-cd-title");
    title.contentEditable = !this.readOnly ? "true" : "false";
    title.innerHTML = this.data.title;
    title.addEventListener("input", () => (this.data.title = title.innerHTML));
    container.appendChild(title);

    const grid = document.createElement("div");
    grid.classList.add("doclib-cd-grid");

    const createBox = (labelStr: string) => {
      const box = document.createElement("div");
      box.classList.add("doclib-cd-box");
      const num = document.createElement("div");
      num.classList.add("doclib-cd-num");
      num.innerText = "00";
      const label = document.createElement("div");
      label.classList.add("doclib-cd-label");
      label.innerText = labelStr;
      box.appendChild(num);
      box.appendChild(label);
      return { box, num };
    };

    const dBox = createBox("Days");
    const hBox = createBox("Hours");
    const mBox = createBox("Minutes");
    const sBox = createBox("Seconds");

    grid.appendChild(dBox.box);
    grid.appendChild(hBox.box);
    grid.appendChild(mBox.box);
    grid.appendChild(sBox.box);
    container.appendChild(grid);

    if (!this.readOnly) {
      const editDiv = document.createElement("div");
      editDiv.classList.add("doclib-cd-edit");
      const input = document.createElement("input");
      input.type = "datetime-local";
      input.classList.add("doclib-cd-input");

      try {
        const d = new Date(this.data.targetDate);
        input.value = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16);
      } catch (e) {}

      input.addEventListener("change", () => {
        this.data.targetDate = new Date(input.value).toISOString();
        this.updateTimer(dBox.num, hBox.num, mBox.num, sBox.num);
      });
      editDiv.appendChild(input);
      container.appendChild(editDiv);
    }

    this.wrapper.appendChild(container);

    this.updateTimer(dBox.num, hBox.num, mBox.num, sBox.num);
    if (this.timerId) clearInterval(this.timerId);
    this.timerId = setInterval(
      () => this.updateTimer(dBox.num, hBox.num, mBox.num, sBox.num),
      1000,
    );
  }

  private updateTimer(
    d: HTMLElement,
    h: HTMLElement,
    m: HTMLElement,
    s: HTMLElement,
  ) {
    const target = new Date(this.data.targetDate).getTime();
    const now = new Date().getTime();
    const diff = target - now;

    if (diff <= 0) {
      d.innerText = "00";
      h.innerText = "00";
      m.innerText = "00";
      s.innerText = "00";
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    d.innerText = days.toString().padStart(2, "0");
    h.innerText = hours.toString().padStart(2, "0");
    m.innerText = minutes.toString().padStart(2, "0");
    s.innerText = seconds.toString().padStart(2, "0");
  }

  save() {
    return this.data;
  }
}
