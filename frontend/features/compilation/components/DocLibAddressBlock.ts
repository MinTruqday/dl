import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibAddressBlock implements BlockTool {
  static readonly feature = {
    id: "DocLibAddressBlock",
    title: "Address Block",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a707108168c85494"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="18,11 20,14 6,17 20,16 16,16 10,13"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Address Block",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a707108168c85494"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="18,11 20,14 6,17 20,16 16,16 10,13"/></svg>',
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
      name: data?.name || "",
      company: data?.company || "",
      street: data?.street || "",
      city: data?.city || "",
      country: data?.country || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-address { font-family: "Times New Roman", serif; font-size: 16px; line-height: 1.5; padding: 24px; border: 1px dashed #cbd5e1; border-radius: 4px; background: #fafafa; margin: 16px 0; max-width: 400px; display: flex; flex-direction: column; gap: 4px; }
      .doclib-address.readonly { border-color: transparent; background: transparent; padding: 0; }
      .doclib-address-line { outline: none; }
      .doclib-address-line:empty:before { content: attr(data-placeholder); color: #94a3b8; font-style: italic; }
      .doclib-address-name { font-weight: bold; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-address");
    if (this.readOnly) container.classList.add("readonly");

    const fields = [
      {
        key: "name",
        cls: "doclib-address-name",
        placeholder: "«DocLib First Last»",
      },
      {
        key: "company",
        cls: "doclib-address-line",
        placeholder: "«DocLib Company Name»",
      },
      {
        key: "street",
        cls: "doclib-address-line",
        placeholder: "«DocLib Street Address»",
      },
      {
        key: "city",
        cls: "doclib-address-line",
        placeholder: "«DocLib City, State ZIP»",
      },
      {
        key: "country",
        cls: "doclib-address-line",
        placeholder: "«DocLib Country»",
      },
    ];

    fields.forEach((f) => {
      const el = document.createElement("div");
      el.classList.add(f.cls);
      el.innerText = this.data[f.key];
      el.dataset.placeholder = f.placeholder;

      if (!this.readOnly) {
        el.contentEditable = "true";
        el.addEventListener("input", () => {
          this.data[f.key] = el.innerText;
        });
      } else {
        if (!this.data[f.key]) el.style.display = "none";
      }

      container.appendChild(el);
    });

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
