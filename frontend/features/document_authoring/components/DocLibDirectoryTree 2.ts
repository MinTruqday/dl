import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDirectoryTree implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Directory Tree",
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
      tree: data?.tree || `src/
  components/
    Button.tsx
  index.ts
package.json`,
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
