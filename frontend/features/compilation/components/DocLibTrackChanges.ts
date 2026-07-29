import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTrackChanges implements BlockTool {
  static readonly feature = {
    id: "DocLibTrackChanges",
    title: "DocLib TrackChanges",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="945705fa865bffe0"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="16,6 9,16 19,10 4,7 7,18 18,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Track Changes",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="945705fa865bffe0"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="16,6 9,16 19,10 4,7 7,18 18,14"/></svg>',
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
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      type: data?.type || "Addition",
      text: data?.text || "",
      author: data?.author || "DocLib User",
      time: data?.time || "Just now",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-tc { font-family: "Times New Roman", serif; font-size: 16px; padding: 4px 8px; margin: 8px 0; border-left: 2px solid transparent; display: inline-block; position: relative; }
      .doclib-tc.add { color: #16a34a; text-decoration: underline; border-left-color: #16a34a; }
      .doclib-tc.del { color: #dc2626; text-decoration: line-through; border-left-color: #dc2626; }
      .doclib-tc-text { outline: none; display: inline-block; }
      .doclib-tc-text:empty:before { content: "DocLib Tracked Text"; color: #94a3b8; font-style: italic; }
      .doclib-tc-meta { position: absolute; left: 100%; top: 0; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 8px; font-family: sans-serif; font-size: 10px; color: #64748b; white-space: nowrap; margin-left: 12px; display: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); z-index: 10; }
      .doclib-tc:hover .doclib-tc-meta { display: block; }
      .doclib-tc-cfg { font-family: sans-serif; font-size: 12px; margin-bottom: 8px; display: flex; gap: 8px; }
      .doclib-tc-select { padding: 2px 4px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");

    if (!this.readOnly) {
      const cfg = document.createElement("div");
      cfg.classList.add("doclib-tc-cfg");
      const sel = document.createElement("select");
      sel.classList.add("doclib-tc-select");
      ["Addition", "Deletion"].forEach((opt) => {
        const o = document.createElement("option");
        o.value = opt;
        o.innerText = opt;
        if (this.data.type === opt) o.selected = true;
        sel.appendChild(o);
      });
      sel.addEventListener("change", () => {
        this.data.type = sel.value;
        tc.className =
          "doclib-tc " + (this.data.type === "Addition" ? "add" : "del");
        meta.innerHTML = `<b>${this.data.author}</b>: ${this.data.type} - ${this.data.time}`;
      });
      cfg.appendChild(sel);
      container.appendChild(cfg);
    }

    const tc = document.createElement("div");
    tc.className =
      "doclib-tc " + (this.data.type === "Addition" ? "add" : "del");

    const text = document.createElement("span");
    text.classList.add("doclib-tc-text");
    text.innerText = this.data.text;
    if (!this.readOnly) {
      text.contentEditable = "true";
      text.addEventListener("input", () => {
        this.data.text = text.innerText;
      });
    }
    tc.appendChild(text);

    const meta = document.createElement("div");
    meta.classList.add("doclib-tc-meta");
    meta.innerHTML = `<b>${this.data.author}</b>: ${this.data.type} - ${this.data.time}`;
    tc.appendChild(meta);

    container.appendChild(tc);
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
