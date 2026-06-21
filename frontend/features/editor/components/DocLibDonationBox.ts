import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDonationBox implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Donation Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      title: data?.title || "",
      desc: data?.desc || "",
      amounts: data?.amounts && data.amounts.length > 0 ? data.amounts : ["$5", "$10", "$50"],
      customLabel: data?.customLabel || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-don-box { max-width: 400px; padding: 24px; border-radius: 12px; background: #fff; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin: 16px auto; font-family: sans-serif; }
      .doclib-don-title { font-size: 24px; font-weight: 700; color: #1e293b; text-align: center; margin-bottom: 8px; outline: none; }
      .doclib-don-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-desc { font-size: 14px; color: #64748b; text-align: center; margin-bottom: 24px; outline: none; }
      .doclib-don-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
      .doclib-don-amt { padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; text-align: center; font-weight: 600; color: #334155; outline: none; cursor: pointer; transition: all 0.2s; }
      .doclib-don-amt:focus, .doclib-don-amt:hover { border-color: #10b981; color: #10b981; }
      .doclib-don-custom { width: 100%; padding: 12px; border: 2px solid #e2e8f0; border-radius: 8px; font-weight: 600; color: #334155; text-align: center; outline: none; margin-bottom: 24px; }
      .doclib-don-custom:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-don-btn { width: 100%; padding: 14px; background: #10b981; color: #fff; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const box = document.createElement("div");
    box.classList.add("doclib-don-box");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-don-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Donation Title";

    const descEl = document.createElement("div");
    descEl.classList.add("doclib-don-desc");
    descEl.innerText = this.data.desc;
    descEl.dataset.placeholder = "DocLib Description";

    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => { this.data.title = titleEl.innerText; });
      descEl.contentEditable = "true";
      descEl.addEventListener("input", () => { this.data.desc = descEl.innerText; });
    }

    const grid = document.createElement("div");
    grid.classList.add("doclib-don-grid");

    this.data.amounts.forEach((amt: string, i: number) => {
      const amtEl = document.createElement("div");
      amtEl.classList.add("doclib-don-amt");
      amtEl.innerText = amt;
      if (!this.readOnly) {
        amtEl.contentEditable = "true";
        amtEl.addEventListener("input", () => { this.data.amounts[i] = amtEl.innerText; });
      }
      grid.appendChild(amtEl);
    });

    const custom = document.createElement("div");
    custom.classList.add("doclib-don-custom");
    custom.innerText = this.data.customLabel;
    custom.dataset.placeholder = "DocLib Custom Amount";
    if (!this.readOnly) {
      custom.contentEditable = "true";
      custom.addEventListener("input", () => { this.data.customLabel = custom.innerText; });
    }

    const btn = document.createElement("button");
    btn.classList.add("doclib-don-btn");
    btn.innerText = "Donate Now";

    box.appendChild(titleEl);
    box.appendChild(descEl);
    box.appendChild(grid);
    box.appendChild(custom);
    box.appendChild(btn);

    this.wrapper.appendChild(box);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
