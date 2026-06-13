import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDivider implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { style: "solid" | "dashed" | "dotted" | "waves" };

  static get toolbox() {
    return {
      title: "DocLib Divider",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      style: data.style || "solid",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-divider-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-divider-styles";
      style.innerHTML = `
            .doclib-dv-wrapper { padding: 16px 0; width: 100%; display: flex; justify-content: center; }
            .doclib-dv-line { width: 100%; height: 2px; }
            .doclib-dv-solid { background: #e2e8f0; }
            .doclib-dv-dashed { border-top: 2px dashed #cbd5e1; }
            .doclib-dv-dotted { border-top: 4px dotted #cbd5e1; }
            .doclib-dv-waves { height: 10px; background-image: radial-gradient(circle at 10px 0, transparent 12px, #e2e8f0 13px); background-size: 20px 10px; background-repeat: repeat-x; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");
    const styles = [
      { name: "solid", icon: "―" },
      { name: "dashed", icon: "---" },
      { name: "dotted", icon: "•••" },
      { name: "waves", icon: "~~~" },
    ];

    styles.forEach((s) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      if (this.data.style === s.name)
        btn.classList.add(this.api.styles.settingsButtonActive);
      btn.innerHTML = `<span style="font-weight:900;">${s.icon}</span>`;
      btn.addEventListener("click", () => {
        this.data.style = s.name as any;
        this.buildUI();
      });
      wrapper.appendChild(btn);
    });

    return wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-dv-wrapper");

    const line = document.createElement("div");
    line.classList.add("doclib-dv-line");
    line.classList.add(`doclib-dv-${this.data.style}`);

    container.appendChild(line);
    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
