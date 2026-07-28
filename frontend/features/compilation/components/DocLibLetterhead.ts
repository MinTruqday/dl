import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibLetterhead implements BlockTool {
  static readonly feature = {
    id: "DocLibLetterhead",
    title: "DocLib Letterhead",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="11908698bcde9d29"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="4,12 19,20 5,5 8,11 6,9 17,9"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Letterhead",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="11908698bcde9d29"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="4,12 19,20 5,5 8,11 6,9 17,9"/></svg>',
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
      companyName: data?.companyName || "",
      address: data?.address || "",
      contact: data?.contact || "",
      logoUrl: data?.logoUrl || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-letterhead { display: flex; justify-content: space-between; align-items: flex-start; padding: 24px 0; border-bottom: 3px double #cbd5e1; margin-bottom: 32px; }
      .doclib-letterhead-left { display: flex; gap: 16px; align-items: center; max-width: 60%; }
      .doclib-letterhead-logo { width: 64px; height: 64px; object-fit: contain; background: #f1f5f9; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #94a3b8; }
      .doclib-letterhead-info { display: flex; flex-direction: column; gap: 4px; }
      .doclib-letterhead-company { font-size: 24px; font-weight: 800; color: #0f172a; text-transform: uppercase; outline: none; }
      .doclib-letterhead-address { font-size: 14px; color: #475569; outline: none; }
      .doclib-letterhead-contact { text-align: right; font-size: 14px; color: #475569; display: flex; flex-direction: column; gap: 4px; outline: none; white-space: pre-wrap; }
      
      .doclib-letterhead-company:empty::before { content: "DocLib Name"; color: #cbd5e1; pointer-events: none; }
      .doclib-letterhead-address:empty::before { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; }
      .doclib-letterhead-contact:empty::before { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; }
      
      .doclib-letterhead-edit { margin-top: 16px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; gap: 8px; align-items: center; }
      .doclib-letterhead-input { flex: 1; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-letterhead");

    const left = document.createElement("div");
    left.classList.add("doclib-letterhead-left");

    const logo = document.createElement("img");
    logo.classList.add("doclib-letterhead-logo");
    if (this.data.logoUrl) {
      logo.src = this.data.logoUrl;
    } else {
      logo.alt = "LOGO";
    }

    const info = document.createElement("div");
    info.classList.add("doclib-letterhead-info");

    const company = document.createElement("div");
    company.classList.add("doclib-letterhead-company");
    company.innerText = this.data.companyName;

    const address = document.createElement("div");
    address.classList.add("doclib-letterhead-address");
    address.innerText = this.data.address;

    info.appendChild(company);
    info.appendChild(address);
    left.appendChild(logo);
    left.appendChild(info);

    const contact = document.createElement("div");
    contact.classList.add("doclib-letterhead-contact");
    contact.innerText = this.data.contact;

    if (!this.readOnly) {
      company.contentEditable = "true";
      address.contentEditable = "true";
      contact.contentEditable = "true";

      company.addEventListener("input", () => {
        this.data.companyName = company.innerText;
      });
      address.addEventListener("input", () => {
        this.data.address = address.innerText;
      });
      contact.addEventListener("input", () => {
        this.data.contact = contact.innerText;
      });
    }

    container.appendChild(left);
    container.appendChild(contact);
    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-letterhead-edit");

      const logoInput = document.createElement("input");
      logoInput.classList.add("doclib-letterhead-input");
      logoInput.placeholder = "DocLib URL";
      logoInput.value = this.data.logoUrl;
      logoInput.addEventListener("input", () => {
        this.data.logoUrl = logoInput.value;
        if (this.data.logoUrl) logo.src = this.data.logoUrl;
        else logo.removeAttribute("src");
      });

      edit.appendChild(logoInput);
      this.wrapper.appendChild(edit);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      companyName: this.data.companyName,
      address: this.data.address,
      contact: this.data.contact,
      logoUrl: this.data.logoUrl,
    };
  }
}
