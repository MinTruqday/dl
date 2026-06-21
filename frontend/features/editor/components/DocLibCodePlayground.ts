import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCodePlayground implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { html: string; css: string; js: string; activeTab: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Code Playground",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline><line x1="12" y1="2" x2="12" y2="22"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      html: data?.html || "<h1>Hello DocLib!</h1>\n<p>Edit this HTML</p>",
      css: data?.css || "body {\n  font-family: sans-serif;\n  padding: 20px;\n  color: #1e293b;\n}",
      js: data?.js || "document.querySelector('h1').style.color = '#0284c7';",
      activeTab: data?.activeTab || "html",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-cp-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-cp-styles";
      style.innerHTML = `
        .doclib-cp-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 12px 0; }
        .doclib-cp-tabs { display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
        .doclib-cp-tab { padding: 9px 18px; font-size: 12px; font-weight: 600; cursor: pointer; border-right: 1px solid #e2e8f0; color: #64748b; user-select: none; }
        .doclib-cp-tab.active { background: #fff; color: #0f172a; border-bottom: 2px solid #0284c7; margin-bottom: -1px; }
        .doclib-cp-tab-html.active { border-bottom-color: #f97316; }
        .doclib-cp-tab-css.active { border-bottom-color: #0284c7; }
        .doclib-cp-tab-js.active { border-bottom-color: #eab308; }
        .doclib-cp-editor { display: none; }
        .doclib-cp-editor.active { display: block; }
        .doclib-cp-textarea { width: 100%; height: 160px; padding: 14px 16px; border: none; outline: none; font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.6; background: #0f172a; color: #e2e8f0; resize: vertical; box-sizing: border-box; tab-size: 2; }
        .doclib-cp-run-row { display: flex; justify-content: flex-end; padding: 8px 12px; background: #f8fafc; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
        .doclib-cp-run-btn { padding: 6px 16px; background: #059669; color: #fff; border: none; border-radius: 5px; font-size: 12px; font-weight: 600; cursor: pointer; }
        .doclib-cp-run-btn:hover { background: #047857; }
        .doclib-cp-preview { width: 100%; height: 220px; border: none; background: #fff; display: block; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private runPreview(iframe: HTMLIFrameElement) {
    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) return;
    doc.open();
    doc.write(`<!DOCTYPE html><html><head><style>${this.data.css}</style></head><body>${this.data.html}<script>${this.data.js}<\/script></body></html>`);
    doc.close();
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-cp-wrapper");

    const tabs = document.createElement("div");
    tabs.classList.add("doclib-cp-tabs");

    const tabDefs = [
      { id: "html", label: "HTML" },
      { id: "css", label: "CSS" },
      { id: "js", label: "JS" },
    ];

    const editors: Record<string, HTMLElement> = {};
    const editorArea = document.createElement("div");

    tabDefs.forEach(({ id, label }) => {
      const tab = document.createElement("div");
      tab.classList.add("doclib-cp-tab", `doclib-cp-tab-${id}`);
      if (this.data.activeTab === id) tab.classList.add("active");
      tab.innerText = label;
      tab.addEventListener("click", () => {
        this.data.activeTab = id;
        tabs.querySelectorAll(".doclib-cp-tab").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        Object.values(editors).forEach((e) => e.classList.remove("active"));
        editors[id].classList.add("active");
      });
      tabs.appendChild(tab);

      const editorDiv = document.createElement("div");
      editorDiv.classList.add("doclib-cp-editor");
      if (this.data.activeTab === id) editorDiv.classList.add("active");

      const textarea = document.createElement("textarea");
      textarea.classList.add("doclib-cp-textarea");
      textarea.value = (this.data as any)[id];
      textarea.readOnly = !!this.readOnly;
      textarea.addEventListener("input", () => {
        (this.data as any)[id] = textarea.value;
      });
      textarea.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
          e.preventDefault();
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          textarea.value = textarea.value.substring(0, start) + "  " + textarea.value.substring(end);
          textarea.selectionStart = textarea.selectionEnd = start + 2;
          (this.data as any)[id] = textarea.value;
        }
      });

      editorDiv.appendChild(textarea);
      editors[id] = editorDiv;
      editorArea.appendChild(editorDiv);
    });

    const runRow = document.createElement("div");
    runRow.classList.add("doclib-cp-run-row");
    const runBtn = document.createElement("button");
    runBtn.classList.add("doclib-cp-run-btn");
    runBtn.innerText = " Run";
    runRow.appendChild(runBtn);

    const iframe = document.createElement("iframe");
    iframe.classList.add("doclib-cp-preview");
    iframe.sandbox.add("allow-scripts");

    runBtn.addEventListener("click", () => this.runPreview(iframe));

    this.wrapper.appendChild(tabs);
    this.wrapper.appendChild(editorArea);
    this.wrapper.appendChild(runRow);
    this.wrapper.appendChild(iframe);

    this.runPreview(iframe);
  }

  save() {
    return this.data;
  }
}
