import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCodeBox implements BlockTool {
  static readonly feature = {
    id: "DocLibCodeBox",
    title: "DocLib Code Box",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4e1fd918f75b8b03"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="14,18 17,11 13,10 7,7 16,13 5,8"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string; language: string; theme: string };

  static get toolbox() {
    return {
      title: "DocLib Code Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4e1fd918f75b8b03"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="14,18 17,11 13,10 7,7 16,13 5,8"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      code: data.code || "",
      language: data.language || "",
      theme: data.theme || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-codebox-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-codebox-styles";
      style.innerHTML = `
            .doclib-codebox-wrapper { background: #1e293b; border-radius: 8px; overflow: hidden; margin: 16px 0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
            .doclib-codebox-header { display: flex; justify-content: space-between; padding: 8px 16px; background: #0f172a; align-items: center; border-bottom: 1px solid #334155; }
            .doclib-codebox-lang { background: transparent; color: #94a3b8; border: none; font-size: 12px; outline: none; font-weight: 600; cursor: pointer; text-transform: uppercase; }
            .doclib-codebox-lang option { background: #0f172a; color: #f8fafc; }
            .doclib-codebox-textarea { width: 100%; min-height: 150px; background: transparent; color: #f8fafc; padding: 16px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 14px; border: none; outline: none; resize: vertical; line-height: 1.5; tab-size: 4; }
            .doclib-codebox-dots { display: flex; gap: 6px; }
            .doclib-codebox-dot { width: 12px; height: 12px; border-radius: 50%; }
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
    container.classList.add("doclib-codebox-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-codebox-header");

    const dots = document.createElement("div");
    dots.classList.add("doclib-codebox-dots");
    dots.innerHTML = `
          <div class="doclib-codebox-dot" style="background: #ef4444;"></div>
          <div class="doclib-codebox-dot" style="background: #eab308;"></div>
          <div class="doclib-codebox-dot" style="background: #22c55e;"></div>
      `;

    const langSelect = document.createElement("select");
    langSelect.classList.add("doclib-codebox-lang");
    const langs = [
      "javascript",
      "typescript",
      "html",
      "css",
      "python",
      "java",
      "c",
      "cpp",
      "go",
      "rust",
      "sql",
      "bash",
      "json",
      "plaintext",
    ];
    langs.forEach((lang) => {
      const opt = document.createElement("option");
      opt.value = lang;
      opt.innerText = lang.toUpperCase();
      if (lang === this.data.language) opt.selected = true;
      langSelect.appendChild(opt);
    });
    langSelect.addEventListener(
      "change",
      () => (this.data.language = langSelect.value),
    );

    header.appendChild(dots);
    header.appendChild(langSelect);

    const textarea = document.createElement("textarea");
    textarea.classList.add("doclib-codebox-textarea");
    textarea.value = this.data.code;
    textarea.placeholder = "DocLib Code";
    textarea.spellcheck = false;

    textarea.addEventListener("input", () => (this.data.code = textarea.value));

    textarea.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        textarea.value =
          textarea.value.substring(0, start) +
          "    " +
          textarea.value.substring(end);
        textarea.selectionStart = textarea.selectionEnd = start + 4;
        this.data.code = textarea.value;
      }
    });

    container.appendChild(header);
    container.appendChild(textarea);
    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
