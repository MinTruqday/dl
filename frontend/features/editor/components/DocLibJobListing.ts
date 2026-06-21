import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibJobListing implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Job Listing",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      role: data?.role || "",
      company: data?.company || "",
      location: data?.location || "",
      type: data?.type || "",
      salary: data?.salary || "",
      btnText: data?.btnText || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-job { font-family: sans-serif; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; max-width: 600px; margin: 16px auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .doclib-job-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
      .doclib-job-role { font-size: 20px; font-weight: bold; color: #0f172a; margin-bottom: 4px; outline: none; }
      .doclib-job-role:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-job-company { font-size: 16px; color: #3b82f6; font-weight: 500; outline: none; }
      .doclib-job-company:empty:before { content: attr(data-placeholder); color: #93c5fd; }
      .doclib-job-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
      .doclib-job-tag { padding: 4px 12px; background: #f1f5f9; border-radius: 16px; font-size: 13px; color: #475569; display: flex; align-items: center; gap: 6px; outline: none; }
      .doclib-job-tag:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-job-btn { padding: 10px 24px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; outline: none; }
      .doclib-job-btn:empty:before { content: attr(data-placeholder); color: rgba(255,255,255,0.7); }
    `;
    this.wrapper.appendChild(style);

    const card = document.createElement("div");
    card.classList.add("doclib-job");

    const top = document.createElement("div");
    top.classList.add("doclib-job-top");

    const info = document.createElement("div");
    
    const roleEl = document.createElement("div");
    roleEl.classList.add("doclib-job-role");
    roleEl.innerText = this.data.role;
    roleEl.dataset.placeholder = "DocLib Job Title";

    const compEl = document.createElement("div");
    compEl.classList.add("doclib-job-company");
    compEl.innerText = this.data.company;
    compEl.dataset.placeholder = "DocLib Company Name";

    if (!this.readOnly) {
      roleEl.contentEditable = "true";
      roleEl.addEventListener("input", () => { this.data.role = roleEl.innerText; });
      compEl.contentEditable = "true";
      compEl.addEventListener("input", () => { this.data.company = compEl.innerText; });
    }

    info.appendChild(roleEl);
    info.appendChild(compEl);
    
    const btn = document.createElement("button");
    btn.classList.add("doclib-job-btn");
    btn.innerText = this.data.btnText;
    btn.dataset.placeholder = "Apply Now";
    if (!this.readOnly) {
      btn.contentEditable = "true";
      btn.addEventListener("input", () => { this.data.btnText = btn.innerText; });
    }

    top.appendChild(info);
    top.appendChild(btn);
    card.appendChild(top);

    const tags = document.createElement("div");
    tags.classList.add("doclib-job-tags");

    const createTag = (key: string, icon: string, placeholder: string) => {
      const tag = document.createElement("div");
      tag.classList.add("doclib-job-tag");
      tag.innerHTML = `<span>${icon}</span> <span class="doclib-job-tag-text" data-placeholder="${placeholder}">${this.data[key]}</span>`;
      const textNode = tag.querySelector(".doclib-job-tag-text") as HTMLElement;
      if (!this.readOnly) {
        textNode.contentEditable = "true";
        textNode.addEventListener("input", () => { this.data[key] = textNode.innerText; });
      }
      return tag;
    };

    tags.appendChild(createTag("location", "📍", "DocLib Location"));
    tags.appendChild(createTag("type", "💼", "DocLib Type"));
    tags.appendChild(createTag("salary", "💰", "DocLib Salary"));
    card.appendChild(tags);

    this.wrapper.appendChild(card);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
