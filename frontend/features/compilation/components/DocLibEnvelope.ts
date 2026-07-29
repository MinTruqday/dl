import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibEnvelope implements BlockTool {
  static readonly feature = {
    id: "DocLibEnvelope",
    title: "Envelope",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0b731206377f4332"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,17 5,10 8,12 20,20 14,17 17,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Envelope",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="0b731206377f4332"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,17 5,10 8,12 20,20 14,17 17,4"/></svg>',
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
      returnAddr: data?.returnAddr || "",
      deliveryAddr: data?.deliveryAddr || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-env { width: 100%; max-width: 600px; height: 300px; background: #fdfdfd; border: 1px solid #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin: 24px auto; position: relative; font-family: Arial, sans-serif; }
      .doclib-env-return { position: absolute; top: 24px; left: 24px; width: 200px; min-height: 50px; font-size: 12px; color: #475569; outline: none; line-height: 1.4; }
      .doclib-env-return:empty:before { content: "DocLib Return Address"; color: #94a3b8; }
      .doclib-env-delivery { position: absolute; top: 120px; left: 200px; right: 40px; min-height: 100px; font-size: 16px; color: #0f172a; outline: none; line-height: 1.5; }
      .doclib-env-delivery:empty:before { content: "DocLib Delivery Address"; color: #94a3b8; }
      .doclib-env-stamp { position: absolute; top: 24px; right: 24px; width: 40px; height: 50px; border: 1px dashed #94a3b8; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #94a3b8; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-env");

    const ret = document.createElement("div");
    ret.classList.add("doclib-env-return");
    ret.innerText = this.data.returnAddr;
    if (!this.readOnly) {
      ret.contentEditable = "true";
      ret.addEventListener("input", () => {
        this.data.returnAddr = ret.innerText;
      });
    }
    container.appendChild(ret);

    const del = document.createElement("div");
    del.classList.add("doclib-env-delivery");
    del.innerText = this.data.deliveryAddr;
    if (!this.readOnly) {
      del.contentEditable = "true";
      del.addEventListener("input", () => {
        this.data.deliveryAddr = del.innerText;
      });
    }
    container.appendChild(del);

    const stamp = document.createElement("div");
    stamp.classList.add("doclib-env-stamp");
    stamp.innerText = "STAMP";
    container.appendChild(stamp);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
