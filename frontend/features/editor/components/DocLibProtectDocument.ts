import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibProtectDocument implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Protect Document",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
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
      level: data?.level || "Unrestricted",
      pwdSet: data?.pwdSet || false,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-protect { font-family: sans-serif; padding: 16px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; margin: 16px 0; max-width: 400px; display: flex; flex-direction: column; gap: 12px; }
      .doclib-protect-head { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 16px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
      .doclib-protect-icon { width: 24px; height: 24px; color: #eab308; }
      .doclib-protect-row { display: flex; align-items: center; justify-content: space-between; font-size: 14px; }
      .doclib-protect-select { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; background: #f8fafc; }
      .doclib-protect-btn { padding: 6px 12px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.3s; }
      .doclib-protect-btn:hover { background: #2563eb; }
      .doclib-protect-btn.active { background: #ef4444; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-protect");

    const head = document.createElement("div");
    head.classList.add("doclib-protect-head");
    head.innerHTML = `<svg class="doclib-protect-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> <span>Protect Document</span>`;
    container.appendChild(head);

    const row1 = document.createElement("div");
    row1.classList.add("doclib-protect-row");
    row1.innerHTML = `<span>Editing Restriction:</span>`;

    const sel = document.createElement("select");
    sel.classList.add("doclib-protect-select");
    if (this.readOnly) sel.disabled = true;
    [
      "Unrestricted",
      "Tracked Changes Only",
      "Comments Only",
      "Read Only",
    ].forEach((opt) => {
      const o = document.createElement("option");
      o.value = opt;
      o.innerText = opt;
      if (this.data.level === opt) o.selected = true;
      sel.appendChild(o);
    });
    if (!this.readOnly) {
      sel.addEventListener("change", () => {
        this.data.level = sel.value;
      });
    }
    row1.appendChild(sel);
    container.appendChild(row1);

    const row2 = document.createElement("div");
    row2.classList.add("doclib-protect-row");
    row2.innerHTML = `<span>Password Protection:</span>`;

    const btn = document.createElement("button");
    btn.classList.add("doclib-protect-btn");
    if (this.data.pwdSet) {
      btn.classList.add("active");
      btn.innerText = "Remove Password";
    } else {
      btn.innerText = "Set Password";
    }

    if (!this.readOnly) {
      btn.addEventListener("click", () => {
        this.data.pwdSet = !this.data.pwdSet;
        if (this.data.pwdSet) {
          btn.classList.add("active");
          btn.innerText = "Remove Password";
        } else {
          btn.classList.remove("active");
          btn.innerText = "Set Password";
        }
      });
    } else {
      btn.disabled = true;
    }
    row2.appendChild(btn);
    container.appendChild(row2);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
