import os

d = '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/features/editor/components'

comps = {
    'DocLibChangelog': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibChangelog implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Changelog",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      version: data?.version || "",
      date: data?.date || "",
      items: data?.items && data.items.length > 0 ? data.items : [{ type: "Added", text: "" }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-clog { font-family: sans-serif; border-left: 2px solid #e2e8f0; margin-left: 12px; padding-left: 24px; position: relative; margin-bottom: 24px; }
      .doclib-clog::before { content: ""; position: absolute; width: 12px; height: 12px; border-radius: 50%; background: #3b82f6; left: -7px; top: 8px; border: 2px solid #fff; }
      .doclib-clog-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
      .doclib-clog-ver { font-size: 20px; font-weight: bold; color: #0f172a; outline: none; }
      .doclib-clog-ver:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-date { font-size: 14px; color: #64748b; outline: none; }
      .doclib-clog-date:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-items { display: flex; flex-direction: column; gap: 8px; }
      .doclib-clog-item { display: flex; align-items: flex-start; gap: 8px; position: relative; }
      .doclib-clog-badge { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; outline: none; cursor: pointer; color: #fff; }
      .doclib-clog-badge[data-type="Added"] { background: #10b981; }
      .doclib-clog-badge[data-type="Fixed"] { background: #ef4444; }
      .doclib-clog-badge[data-type="Changed"] { background: #f59e0b; }
      .doclib-clog-badge[data-type="Deprecated"] { background: #64748b; }
      .doclib-clog-text { flex: 1; font-size: 14px; color: #334155; line-height: 1.5; outline: none; }
      .doclib-clog-text:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-clog-del { background: none; border: none; color: #ef4444; cursor: pointer; font-weight: bold; font-size: 12px; margin-top: 2px; }
      .doclib-clog-add { margin-top: 12px; padding: 6px 12px; font-size: 12px; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const clog = document.createElement("div");
    clog.classList.add("doclib-clog");

    const header = document.createElement("div");
    header.classList.add("doclib-clog-header");

    const verEl = document.createElement("div");
    verEl.classList.add("doclib-clog-ver");
    verEl.innerText = this.data.version;
    verEl.dataset.placeholder = "v1.0.0";
    if (!this.readOnly) {
      verEl.contentEditable = "true";
      verEl.addEventListener("input", () => { this.data.version = verEl.innerText; });
    }

    const dateEl = document.createElement("div");
    dateEl.classList.add("doclib-clog-date");
    dateEl.innerText = this.data.date;
    dateEl.dataset.placeholder = "DocLib Release Date";
    if (!this.readOnly) {
      dateEl.contentEditable = "true";
      dateEl.addEventListener("input", () => { this.data.date = dateEl.innerText; });
    }

    header.appendChild(verEl);
    header.appendChild(dateEl);
    clog.appendChild(header);

    const itemsCont = document.createElement("div");
    itemsCont.classList.add("doclib-clog-items");

    const types = ["Added", "Fixed", "Changed", "Deprecated"];

    const renderItems = () => {
      itemsCont.innerHTML = "";
      this.data.items.forEach((item: any, i: number) => {
        const itemEl = document.createElement("div");
        itemEl.classList.add("doclib-clog-item");

        const badge = document.createElement("div");
        badge.classList.add("doclib-clog-badge");
        badge.dataset.type = item.type;
        badge.innerText = item.type;
        if (!this.readOnly) {
          badge.addEventListener("click", () => {
            const currentIdx = types.indexOf(item.type);
            const nextIdx = (currentIdx + 1) % types.length;
            this.data.items[i].type = types[nextIdx];
            renderItems();
          });
        }

        const textEl = document.createElement("div");
        textEl.classList.add("doclib-clog-text");
        textEl.innerText = item.text;
        textEl.dataset.placeholder = "DocLib Changelog description";
        if (!this.readOnly) {
          textEl.contentEditable = "true";
          textEl.addEventListener("input", () => { this.data.items[i].text = textEl.innerText; });

          const delBtn = document.createElement("button");
          delBtn.classList.add("doclib-clog-del");
          delBtn.innerText = "✕";
          delBtn.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderItems();
          });
          
          itemEl.appendChild(badge);
          itemEl.appendChild(textEl);
          itemEl.appendChild(delBtn);
        } else {
          itemEl.appendChild(badge);
          itemEl.appendChild(textEl);
        }

        itemsCont.appendChild(itemEl);
      });
    };

    renderItems();
    clog.appendChild(itemsCont);

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-clog-add");
      addBtn.innerText = "+ Add Item";
      addBtn.addEventListener("click", () => {
        this.data.items.push({ type: "Added", text: "" });
        renderItems();
      });
      clog.appendChild(addBtn);
    }

    this.wrapper.appendChild(clog);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibProductRoadmap': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibProductRoadmap implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib ProductRoadmap",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      q1: data?.q1 || ["DocLib Task 1"],
      q2: data?.q2 || ["DocLib Task 2"],
      q3: data?.q3 || ["DocLib Task 3"],
      q4: data?.q4 || ["DocLib Task 4"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-roadmap { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; font-family: sans-serif; overflow-x: auto; padding-bottom: 8px; }
      .doclib-rm-col { display: flex; flex-direction: column; gap: 8px; background: #f8fafc; border-radius: 8px; padding: 12px; border: 1px solid #e2e8f0; min-width: 200px; }
      .doclib-rm-header { font-size: 16px; font-weight: bold; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; margin-bottom: 8px; text-align: center; }
      .doclib-rm-item { background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px; font-size: 13px; color: #334155; position: relative; }
      .doclib-rm-item-text { outline: none; min-height: 20px; }
      .doclib-rm-item-text:empty:before { content: "DocLib Task..."; color: #94a3b8; }
      .doclib-rm-del { position: absolute; right: 4px; top: 4px; background: none; border: none; font-size: 10px; color: #ef4444; cursor: pointer; display: none; }
      .doclib-rm-item:hover .doclib-rm-del { display: block; }
      .doclib-rm-add { background: none; border: 1px dashed #cbd5e1; color: #64748b; padding: 8px; font-size: 12px; cursor: pointer; border-radius: 4px; text-align: center; }
      .doclib-rm-add:hover { background: #e2e8f0; }
    `;
    this.wrapper.appendChild(style);

    const roadmap = document.createElement("div");
    roadmap.classList.add("doclib-roadmap");

    const quarters = ["q1", "q2", "q3", "q4"];
    const titles = ["Q1", "Q2", "Q3", "Q4"];

    const renderUI = () => {
      roadmap.innerHTML = "";
      quarters.forEach((q, idx) => {
        const col = document.createElement("div");
        col.classList.add("doclib-rm-col");

        const header = document.createElement("div");
        header.classList.add("doclib-rm-header");
        header.innerText = titles[idx];
        col.appendChild(header);

        this.data[q].forEach((task: string, tIdx: number) => {
          const item = document.createElement("div");
          item.classList.add("doclib-rm-item");

          const text = document.createElement("div");
          text.classList.add("doclib-rm-item-text");
          text.innerText = task;
          if (!this.readOnly) {
            text.contentEditable = "true";
            text.addEventListener("input", () => { this.data[q][tIdx] = text.innerText; });

            const delBtn = document.createElement("button");
            delBtn.classList.add("doclib-rm-del");
            delBtn.innerText = "✕";
            delBtn.addEventListener("click", () => {
              this.data[q].splice(tIdx, 1);
              renderUI();
            });
            item.appendChild(delBtn);
          }
          item.appendChild(text);
          col.appendChild(item);
        });

        if (!this.readOnly) {
          const addBtn = document.createElement("button");
          addBtn.classList.add("doclib-rm-add");
          addBtn.innerText = "+ Add Task";
          addBtn.addEventListener("click", () => {
            this.data[q].push("");
            renderUI();
          });
          col.appendChild(addBtn);
        }

        roadmap.appendChild(col);
      });
    };

    renderUI();
    this.wrapper.appendChild(roadmap);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibDirectoryTree': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDirectoryTree implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib DirectoryTree",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line><path d="M13 8h4"></path><path d="M13 12h2"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      tree: data?.tree || "src/\n  components/\n    Button.tsx\n  index.ts\npackage.json",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-dirtree { background: #1e293b; border-radius: 8px; padding: 16px; font-family: monospace; color: #cbd5e1; font-size: 14px; position: relative; }
      .doclib-dirtree-textarea { width: 100%; min-height: 150px; background: transparent; border: none; color: #cbd5e1; font-family: inherit; font-size: inherit; resize: vertical; outline: none; line-height: 1.5; white-space: pre; }
      .doclib-dirtree-view { white-space: pre; line-height: 1.5; }
      .doclib-dirtree-label { position: absolute; top: -10px; right: 16px; background: #3b82f6; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-family: sans-serif; font-weight: bold; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-dirtree");

    const label = document.createElement("div");
    label.classList.add("doclib-dirtree-label");
    label.innerText = "DIRECTORY TREE";
    container.appendChild(label);

    if (!this.readOnly) {
      const textarea = document.createElement("textarea");
      textarea.classList.add("doclib-dirtree-textarea");
      textarea.value = this.data.tree;
      textarea.spellcheck = false;
      textarea.placeholder = "DocLib Folder Tree (Use spaces for indent)";
      textarea.addEventListener("input", () => {
        this.data.tree = textarea.value;
      });
      container.appendChild(textarea);
    } else {
      const view = document.createElement("div");
      view.classList.add("doclib-dirtree-view");
      view.innerText = this.data.tree;
      container.appendChild(view);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibJsonViewer': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibJsonViewer implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib JsonViewer",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      jsonStr: data?.jsonStr || '{\n  "doclib": "awesome",\n  "version": 1\n}',
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-json { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 13px; color: #0f172a; position: relative; }
      .doclib-json-textarea { width: 100%; min-height: 150px; background: transparent; border: none; font-family: inherit; font-size: inherit; resize: vertical; outline: none; line-height: 1.5; color: #0f172a; }
      .doclib-json-label { position: absolute; top: -10px; right: 16px; background: #f59e0b; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-family: sans-serif; font-weight: bold; }
      .doclib-json-error { color: #ef4444; font-size: 11px; margin-top: 8px; font-family: sans-serif; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-json");

    const label = document.createElement("div");
    label.classList.add("doclib-json-label");
    label.innerText = "JSON";
    container.appendChild(label);

    const errorMsg = document.createElement("div");
    errorMsg.classList.add("doclib-json-error");

    if (!this.readOnly) {
      const textarea = document.createElement("textarea");
      textarea.classList.add("doclib-json-textarea");
      textarea.value = this.data.jsonStr;
      textarea.spellcheck = false;
      textarea.addEventListener("input", () => {
        this.data.jsonStr = textarea.value;
        try {
          JSON.parse(this.data.jsonStr);
          errorMsg.innerText = "";
        } catch (e: any) {
          errorMsg.innerText = "Invalid JSON: " + e.message;
        }
      });
      container.appendChild(textarea);
      container.appendChild(errorMsg);
    } else {
      const view = document.createElement("pre");
      view.style.margin = "0";
      try {
        const obj = JSON.parse(this.data.jsonStr);
        view.innerText = JSON.stringify(obj, null, 2);
      } catch (e) {
        view.innerText = this.data.jsonStr;
      }
      container.appendChild(view);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
""",
    'DocLibMarkdownBlock': """import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMarkdownBlock implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib MarkdownBlock",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      md: data?.md || "# DocLib Markdown\\n\\nType your **markdown** here.",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-md { display: flex; flex-direction: column; gap: 8px; font-family: sans-serif; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; }
      .doclib-md-tabs { display: flex; background: #f8fafc; border-bottom: 1px solid #cbd5e1; }
      .doclib-md-tab { padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: bold; color: #64748b; }
      .doclib-md-tab.active { background: #fff; color: #0f172a; border-bottom: 2px solid #3b82f6; }
      .doclib-md-content { padding: 16px; min-height: 150px; }
      .doclib-md-textarea { width: 100%; height: 100%; min-height: 150px; background: transparent; border: none; font-family: monospace; font-size: 14px; resize: vertical; outline: none; line-height: 1.5; color: #0f172a; }
      .doclib-md-preview { font-family: sans-serif; }
      .doclib-md-preview h1 { font-size: 2em; margin-bottom: 0.5em; }
      .doclib-md-preview h2 { font-size: 1.5em; margin-bottom: 0.5em; }
      .doclib-md-preview p { margin-bottom: 1em; }
      .doclib-md-preview strong { font-weight: bold; }
      .doclib-md-preview em { font-style: italic; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-md");

    let isEditMode = !this.readOnly;

    const tabs = document.createElement("div");
    tabs.classList.add("doclib-md-tabs");

    const editTab = document.createElement("div");
    editTab.classList.add("doclib-md-tab");
    editTab.innerText = "Edit";
    
    const prevTab = document.createElement("div");
    prevTab.classList.add("doclib-md-tab");
    prevTab.innerText = "Preview";

    if (!this.readOnly) {
      tabs.appendChild(editTab);
      tabs.appendChild(prevTab);
      container.appendChild(tabs);
    }

    const contentArea = document.createElement("div");
    contentArea.classList.add("doclib-md-content");
    container.appendChild(contentArea);

    const renderUI = () => {
      contentArea.innerHTML = "";
      if (isEditMode) {
        editTab.classList.add("active");
        prevTab.classList.remove("active");
        
        const textarea = document.createElement("textarea");
        textarea.classList.add("doclib-md-textarea");
        textarea.value = this.data.md;
        textarea.addEventListener("input", () => {
          this.data.md = textarea.value;
        });
        contentArea.appendChild(textarea);
      } else {
        editTab.classList.remove("active");
        prevTab.classList.add("active");

        const preview = document.createElement("div");
        preview.classList.add("doclib-md-preview");
        // Very basic simple markdown parsing for demo purposes
        let html = this.data.md
          .replace(/^# (.*$)/gim, '<h1>$1</h1>')
          .replace(/^## (.*$)/gim, '<h2>$1</h2>')
          .replace(/\\*\\*(.*?)\\*\\*/gim, '<strong>$1</strong>')
          .replace(/\\*(.*?)\\*/gim, '<em>$1</em>')
          .replace(/\\n$/gim, '<br />');
        
        preview.innerHTML = html;
        contentArea.appendChild(preview);
      }
    };

    if (!this.readOnly) {
      editTab.addEventListener("click", () => { isEditMode = true; renderUI(); });
      prevTab.addEventListener("click", () => { isEditMode = false; renderUI(); });
    }

    renderUI();
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
"""
}

for k, v in comps.items():
    with open(os.path.join(d, k + '.ts'), 'w') as f:
        f.write(v)

print("Created 5 components")
