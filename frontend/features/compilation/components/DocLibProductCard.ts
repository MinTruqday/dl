import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibProductCard implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Product Card",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>',
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
      image: data?.image || "",
      title: data?.title || "",
      price: data?.price || "",
      desc: data?.desc || "",
      btnText: data?.btnText || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-prod-card { display: flex; flex-direction: column; max-width: 350px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; font-family: sans-serif; background: #fff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin: 16px auto; }
      .doclib-prod-img-wrap { width: 100%; height: 250px; background: #f8fafc; display: flex; align-items: center; justify-content: center; position: relative; }
      .doclib-prod-img { width: 100%; height: 100%; object-fit: cover; }
      .doclib-prod-img-placeholder { color: #94a3b8; font-size: 14px; }
      .doclib-prod-content { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
      .doclib-prod-title { font-size: 20px; font-weight: 700; color: #0f172a; outline: none; }
      .doclib-prod-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-price { font-size: 24px; font-weight: 800; color: #2563eb; outline: none; }
      .doclib-prod-price:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-desc { font-size: 14px; color: #475569; line-height: 1.5; outline: none; }
      .doclib-prod-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-prod-btn { width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-weight: 600; font-size: 16px; cursor: pointer; outline: none; text-align: center; }
      .doclib-prod-btn:empty:before { content: attr(data-placeholder); color: rgba(255,255,255,0.7); }
      .doclib-prod-input { position: absolute; top: 8px; right: 8px; padding: 4px 8px; font-size: 12px; border: 1px solid #cbd5e1; border-radius: 4px; z-index: 10; }
    `;
    this.wrapper.appendChild(style);

    const card = document.createElement("div");
    card.classList.add("doclib-prod-card");

    const imgWrap = document.createElement("div");
    imgWrap.classList.add("doclib-prod-img-wrap");

    const img = document.createElement("img");
    img.classList.add("doclib-prod-img");
    const updateImg = () => {
      if (this.data.image) {
        img.src = this.data.image;
        img.style.display = "block";
      } else {
        img.style.display = "none";
      }
    };
    updateImg();

    const placeholder = document.createElement("div");
    placeholder.classList.add("doclib-prod-img-placeholder");
    placeholder.innerText = "DocLib Image Area";

    if (!this.readOnly) {
      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-prod-input");
      urlInput.placeholder = "DocLib Image URL";
      urlInput.value = this.data.image;
      urlInput.addEventListener("input", () => {
        this.data.image = urlInput.value;
        updateImg();
      });
      imgWrap.appendChild(urlInput);
    }

    imgWrap.appendChild(placeholder);
    imgWrap.appendChild(img);
    card.appendChild(imgWrap);

    const content = document.createElement("div");
    content.classList.add("doclib-prod-content");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-prod-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Product Name";
    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => {
        this.data.title = titleEl.innerText;
      });
    }

    const priceEl = document.createElement("div");
    priceEl.classList.add("doclib-prod-price");
    priceEl.innerText = this.data.price;
    priceEl.dataset.placeholder = "DocLib Price";
    if (!this.readOnly) {
      priceEl.contentEditable = "true";
      priceEl.addEventListener("input", () => {
        this.data.price = priceEl.innerText;
      });
    }

    const descEl = document.createElement("div");
    descEl.classList.add("doclib-prod-desc");
    descEl.innerText = this.data.desc;
    descEl.dataset.placeholder = "DocLib Description";
    if (!this.readOnly) {
      descEl.contentEditable = "true";
      descEl.addEventListener("input", () => {
        this.data.desc = descEl.innerText;
      });
    }

    const btnEl = document.createElement("div");
    btnEl.classList.add("doclib-prod-btn");
    btnEl.innerText = this.data.btnText;
    btnEl.dataset.placeholder = "DocLib Button Text";
    if (!this.readOnly) {
      btnEl.contentEditable = "true";
      btnEl.addEventListener("input", () => {
        this.data.btnText = btnEl.innerText;
      });
    }

    content.appendChild(titleEl);
    content.appendChild(priceEl);
    content.appendChild(descEl);
    content.appendChild(btnEl);

    card.appendChild(content);
    this.wrapper.appendChild(card);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
