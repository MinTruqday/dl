import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTypewriter implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { phrases: string[]; speed: number; loop: boolean };
  private readOnly: boolean;
  private animInterval: ReturnType<typeof setInterval> | null = null;

  static get toolbox() {
    return {
      title: "DocLib Typewriter",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      phrases: data?.phrases || [],
      speed: data?.speed || 80,
      loop: data?.loop !== undefined ? data.loop : true,
    };
  }

  private startTypewriter(display: HTMLElement, cursor: HTMLElement) {
    if (this.animInterval) clearInterval(this.animInterval);
    const phrases = this.data.phrases.filter((p) => p.trim());
    if (phrases.length === 0) return;

    let phraseIdx = 0;
    let charIdx = 0;
    let deleting = false;
    let pauseCounter = 0;

    this.animInterval = setInterval(() => {
      const current = phrases[phraseIdx];

      if (pauseCounter > 0) {
        pauseCounter--;
        return;
      }

      if (!deleting) {
        charIdx++;
        display.innerText = current.substring(0, charIdx);
        if (charIdx === current.length) {
          deleting = true;
          pauseCounter = Math.round(1500 / this.data.speed);
        }
      } else {
        charIdx--;
        display.innerText = current.substring(0, charIdx);
        if (charIdx === 0) {
          deleting = false;
          phraseIdx++;
          if (phraseIdx >= phrases.length) {
            if (!this.data.loop) {
              clearInterval(this.animInterval!);
              cursor.style.display = "none";
              return;
            }
            phraseIdx = 0;
          }
          pauseCounter = 3;
        }
      }
    }, this.data.speed);
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-tw-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-tw-styles";
      style.innerHTML = `
        .doclib-tw-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; background: #0f172a; margin: 12px 0; }
        .doclib-tw-display-row { display: flex; align-items: center; gap: 2px; min-height: 40px; }
        .doclib-tw-text { font-size: 22px; font-weight: 700; color: #f8fafc; font-family: ui-monospace, monospace; }
        .doclib-tw-cursor { width: 2px; height: 28px; background: #38bdf8; animation: doclib-tw-blink 1s step-end infinite; }
        @keyframes doclib-tw-blink { 50% { opacity: 0; } }
        .doclib-tw-edit { border-top: 1px solid #1e293b; margin-top: 16px; padding-top: 14px; }
        .doclib-tw-edit-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 6px; }
        .doclib-tw-textarea { width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; font-size: 13px; color: #e2e8f0; outline: none; resize: vertical; min-height: 80px; font-family: ui-monospace, monospace; box-sizing: border-box; }
        .doclib-tw-controls { display: flex; gap: 12px; margin-top: 12px; flex-wrap: wrap; align-items: center; }
        .doclib-tw-speed-row { display: flex; align-items: center; gap: 8px; }
        .doclib-tw-speed-label { font-size: 11px; color: #64748b; }
        .doclib-tw-slider { width: 100px; accent-color: #38bdf8; }
        .doclib-tw-loop-toggle { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #94a3b8; cursor: pointer; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (this.animInterval) { clearInterval(this.animInterval); this.animInterval = null; }
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-tw-wrapper");

    const displayRow = document.createElement("div");
    displayRow.classList.add("doclib-tw-display-row");

    const text = document.createElement("span");
    text.classList.add("doclib-tw-text");

    const cursor = document.createElement("span");
    cursor.classList.add("doclib-tw-cursor");

    displayRow.appendChild(text);
    displayRow.appendChild(cursor);
    this.wrapper.appendChild(displayRow);

    this.startTypewriter(text, cursor);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-tw-edit");

      const label = document.createElement("div");
      label.classList.add("doclib-tw-edit-label");
      label.innerText = "Phrases one per line";

      const textarea = document.createElement("textarea");
      textarea.classList.add("doclib-tw-textarea");
      textarea.value = this.data.phrases.join("\n");

      let timeout: ReturnType<typeof setTimeout>;
      textarea.addEventListener("input", () => {
        this.data.phrases = textarea.value.split("\n").map((p) => p.trim()).filter((p) => p);
        clearTimeout(timeout);
        timeout = setTimeout(() => this.startTypewriter(text, cursor), 600);
      });

      const controls = document.createElement("div");
      controls.classList.add("doclib-tw-controls");

      const speedRow = document.createElement("div");
      speedRow.classList.add("doclib-tw-speed-row");

      const speedLabel = document.createElement("span");
      speedLabel.classList.add("doclib-tw-speed-label");
      speedLabel.innerText = `Speed: ${this.data.speed}ms`;

      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = "30";
      slider.max = "200";
      slider.value = `${this.data.speed}`;
      slider.classList.add("doclib-tw-slider");
      slider.addEventListener("input", () => {
        this.data.speed = parseInt(slider.value);
        speedLabel.innerText = `Speed: ${this.data.speed}ms`;
        this.startTypewriter(text, cursor);
      });

      speedRow.appendChild(speedLabel);
      speedRow.appendChild(slider);

      const loopToggle = document.createElement("label");
      loopToggle.classList.add("doclib-tw-loop-toggle");

      const loopCheck = document.createElement("input");
      loopCheck.type = "checkbox";
      loopCheck.checked = this.data.loop;
      loopCheck.addEventListener("change", () => {
        this.data.loop = loopCheck.checked;
        this.startTypewriter(text, cursor);
      });

      loopToggle.appendChild(loopCheck);
      loopToggle.appendChild(document.createTextNode("Loop"));

      controls.appendChild(speedRow);
      controls.appendChild(loopToggle);

      edit.appendChild(label);
      edit.appendChild(textarea);
      edit.appendChild(controls);
      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
