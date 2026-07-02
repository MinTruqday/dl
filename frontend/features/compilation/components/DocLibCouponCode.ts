import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCouponCode implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Coupon Code",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg>',
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
      title: data?.title || "",
      discount: data?.discount || "",
      code: data?.code || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-coupon { border: 2px dashed #f59e0b; border-radius: 12px; padding: 24px; background: #fffbeb; text-align: center; max-width: 400px; margin: 24px auto; position: relative; font-family: sans-serif; }
      .doclib-coupon::before, .doclib-coupon::after { content: ""; position: absolute; width: 20px; height: 20px; background: #fff; border-radius: 50%; top: 50%; transform: translateY(-50%); border: 2px solid #f59e0b; border-left: none; }
      .doclib-coupon::before { left: -12px; border-radius: 0 10px 10px 0; border: 2px dashed #f59e0b; border-left: none; }
      .doclib-coupon::after { right: -12px; border-radius: 10px 0 0 10px; border: 2px dashed #f59e0b; border-right: none; }
      .doclib-coupon-title { font-size: 16px; color: #b45309; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; outline: none; }
      .doclib-coupon-title:empty:before { content: attr(data-placeholder); color: #d97706; }
      .doclib-coupon-discount { font-size: 36px; font-weight: 900; color: #b45309; margin-bottom: 16px; outline: none; }
      .doclib-coupon-discount:empty:before { content: attr(data-placeholder); color: #d97706; }
      .doclib-coupon-code-wrap { display: flex; align-items: center; justify-content: space-between; background: #fff; border: 1px solid #fcd34d; border-radius: 6px; padding: 8px 16px; }
      .doclib-coupon-code { font-family: monospace; font-size: 18px; font-weight: bold; color: #1e293b; letter-spacing: 2px; outline: none; flex: 1; text-align: left; }
      .doclib-coupon-code:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-coupon-copy { padding: 6px 12px; background: #f59e0b; color: #fff; font-weight: bold; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
    `;
    this.wrapper.appendChild(style);

    const box = document.createElement("div");
    box.classList.add("doclib-coupon");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-coupon-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Promo Title";

    const discEl = document.createElement("div");
    discEl.classList.add("doclib-coupon-discount");
    discEl.innerText = this.data.discount;
    discEl.dataset.placeholder = "DocLib Discount";

    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => {
        this.data.title = titleEl.innerText;
      });
      discEl.contentEditable = "true";
      discEl.addEventListener("input", () => {
        this.data.discount = discEl.innerText;
      });
    }

    const wrap = document.createElement("div");
    wrap.classList.add("doclib-coupon-code-wrap");

    const codeEl = document.createElement("div");
    codeEl.classList.add("doclib-coupon-code");
    codeEl.innerText = this.data.code;
    codeEl.dataset.placeholder = "DOCLIBCODE";

    if (!this.readOnly) {
      codeEl.contentEditable = "true";
      codeEl.addEventListener("input", () => {
        this.data.code = codeEl.innerText;
      });
    }

    const btn = document.createElement("button");
    btn.classList.add("doclib-coupon-copy");
    btn.innerText = "Copy";
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(this.data.code || "DOCLIBCODE").then(() => {
        btn.innerText = "Copied";
        setTimeout(() => {
          btn.innerText = "Copy";
        }, 1500);
      });
    });

    wrap.appendChild(codeEl);
    wrap.appendChild(btn);

    box.appendChild(titleEl);
    box.appendChild(discEl);
    box.appendChild(wrap);

    this.wrapper.appendChild(box);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
