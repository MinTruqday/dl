import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDateAndTime implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Date & Time",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      format: data?.format || "",
      timestamp: data?.timestamp || Date.now(),
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-datetime { display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 16px; font-family: monospace; font-size: 14px; color: #334155; margin: 16px 0; }
      .doclib-datetime-icon { color: #64748b; }
      .doclib-datetime-select { border: none; background: transparent; outline: none; font-family: monospace; font-size: 14px; color: #334155; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-datetime");

    const icon = document.createElement("span");
    icon.classList.add("doclib-datetime-icon");
    icon.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
    container.appendChild(icon);

    const d = new Date(this.data.timestamp);
    const getFormatted = (fmt: string) => {
      if (fmt === "locale") return d.toLocaleString();
      if (fmt === "date") return d.toLocaleDateString();
      if (fmt === "time") return d.toLocaleTimeString();
      if (fmt === "iso") return d.toISOString();
      return d.toDateString();
    };

    if (this.readOnly) {
      const text = document.createElement("span");
      text.innerText = getFormatted(this.data.format);
      container.appendChild(text);
    } else {
      const select = document.createElement("select");
      select.classList.add("doclib-datetime-select");
      
      ["locale", "date", "time", "iso", "string"].forEach(f => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.text = getFormatted(f);
        opt.selected = this.data.format === f;
        select.appendChild(opt);
      });
      
      select.addEventListener("change", () => {
        this.data.format = select.value;
        this.data.timestamp = Date.now();
        Array.from(select.options).forEach(opt => {
          opt.text = getFormatted(opt.value);
        });
      });
      
      container.appendChild(select);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      format: this.data.format,
      timestamp: Date.now(),
    };
  }
}
