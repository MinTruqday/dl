import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibReadingTime implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { avgReadingSpeed: number; label: string };

  static get toolbox() {
    return {
      title: "DocLib Reading Time",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      avgReadingSpeed: data?.avgReadingSpeed || 200,
      label: data?.label || "DocLib Button",
    };
  }

  private countWords(): number {
    try {
      const blocks = (this.api as any).blocks;
      if (!blocks) return 0;
      let text = "";
      for (let i = 0; i < blocks.getBlocksCount(); i++) {
        const block = blocks.getBlockByIndex(i);
        if (block && block.holder) {
          text += " " + (block.holder.innerText || "");
        }
      }
      return text
        .trim()
        .split(/\s+/)
        .filter((w: string) => w.length > 0).length;
    } catch (e) {
      return 0;
    }
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-rt-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-rt-styles";
      style.innerHTML = `
        .doclib-rt-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; background: #f0f9ff; margin: 12px 0; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
        .doclib-rt-icon { font-size: 28px; }
        .doclib-rt-info { flex: 1; }
        .doclib-rt-label { font-size: 12px; font-weight: 600; color: #0284c7; text-transform: uppercase; letter-spacing: 0.05em; }
        .doclib-rt-time { font-size: 24px; font-weight: 700; color: #0c4a6e; }
        .doclib-rt-meta { font-size: 12px; color: #64748b; margin-top: 2px; }
        .doclib-rt-settings { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #64748b; margin-left: auto; }
        .doclib-rt-speed { width: 100px; accent-color: #0284c7; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  renderSettings() {
    const wrap = document.createElement("div");
    const label = document.createElement("div");
    label.style.cssText = "font-size:12px;color:#64748b;padding:8px;";
    label.innerText = "Reading speed (WPM)";

    const speeds = [100, 150, 200, 250, 300, 400];
    speeds.forEach((s) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      if (this.data.avgReadingSpeed === s)
        btn.classList.add(this.api.styles.settingsButtonActive);
      btn.innerText = `${s}`;
      btn.addEventListener("click", () => {
        this.data.avgReadingSpeed = s;
        this.buildUI();
      });
      wrap.appendChild(btn);
    });

    wrap.insertBefore(label, wrap.firstChild);
    return wrap;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-rt-wrapper");

    const wordCount = this.countWords();
    const minutes =
      wordCount > 0
        ? Math.max(1, Math.round(wordCount / this.data.avgReadingSpeed))
        : 0;

    const icon = document.createElement("div");
    icon.classList.add("doclib-rt-icon");
    icon.innerText = "";

    const info = document.createElement("div");
    info.classList.add("doclib-rt-info");

    const label = document.createElement("div");
    label.classList.add("doclib-rt-label");
    label.innerText = this.data.label;

    const time = document.createElement("div");
    time.classList.add("doclib-rt-time");
    time.innerText = wordCount > 0 ? `${minutes} min read` : "No content yet";

    const meta = document.createElement("div");
    meta.classList.add("doclib-rt-meta");
    meta.innerText = `${wordCount.toLocaleString("vi-VN")} words  ${this.data.avgReadingSpeed} WPM`;

    info.appendChild(label);
    info.appendChild(time);
    info.appendChild(meta);

    this.wrapper.appendChild(icon);
    this.wrapper.appendChild(info);
  }

  save() {
    return this.data;
  }
}
