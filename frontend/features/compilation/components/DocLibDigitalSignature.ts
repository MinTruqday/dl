import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDigitalSignature implements BlockTool {
  static readonly feature = {
    id: "DocLibDigitalSignature",
    title: "DocLib Digital Signature",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba1b2e375a980f64"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="20,14 16,8 9,20 19,19 8,15 4,16"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Digital Signature",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba1b2e375a980f64"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="20,14 16,8 9,20 19,19 8,15 4,16"/></svg>',
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
      signer: data?.signer || "",
      issuer: data?.issuer || "DocLib CA",
      date: data?.date || new Date().toISOString().split("T")[0],
      valid: data?.valid !== undefined ? data.valid : true,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-cert { font-family: sans-serif; display: flex; align-items: flex-start; gap: 16px; padding: 16px; border: 2px solid #16a34a; border-radius: 8px; background: #f0fdf4; margin: 16px 0; max-width: 450px; position: relative; }
      .doclib-cert.invalid { border-color: #ef4444; background: #fef2f2; }
      .doclib-cert-icon { width: 40px; height: 40px; color: #16a34a; flex-shrink: 0; }
      .doclib-cert.invalid .doclib-cert-icon { color: #ef4444; }
      .doclib-cert-info { flex: 1; display: flex; flex-direction: column; gap: 4px; }
      .doclib-cert-title { font-size: 16px; font-weight: bold; color: #16a34a; margin-bottom: 4px; }
      .doclib-cert.invalid .doclib-cert-title { color: #dc2626; }
      .doclib-cert-row { font-size: 13px; color: #334155; display: flex; }
      .doclib-cert-lbl { font-weight: 600; width: 80px; }
      .doclib-cert-val { flex: 1; outline: none; }
      .doclib-cert-val:empty:before { content: "DocLib Value"; color: #94a3b8; }
      .doclib-cert-toggle { position: absolute; top: 16px; right: 16px; font-size: 12px; background: #fff; border: 1px solid #cbd5e1; padding: 4px 8px; border-radius: 4px; cursor: pointer; color: #475569; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-cert");
    if (!this.data.valid) container.classList.add("invalid");

    const renderContent = () => {
      container.innerHTML = "";

      const iconStr = this.data.valid
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba1b2e375a980f64"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="20,14 16,8 9,20 19,19 8,15 4,16"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba1b2e375a980f64"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="20,14 16,8 9,20 19,19 8,15 4,16"/></svg>';

      container.innerHTML = iconStr;

      const info = document.createElement("div");
      info.classList.add("doclib-cert-info");

      const title = document.createElement("div");
      title.classList.add("doclib-cert-title");
      title.innerText = this.data.valid
        ? "Valid Digital Signature"
        : "Invalid Digital Signature";
      info.appendChild(title);

      const createRow = (label: string, key: string) => {
        const row = document.createElement("div");
        row.classList.add("doclib-cert-row");
        row.innerHTML = `<span class="doclib-cert-lbl">${label}:</span>`;
        const val = document.createElement("span");
        val.classList.add("doclib-cert-val");
        val.innerText = this.data[key];
        if (!this.readOnly) {
          val.contentEditable = "true";
          val.addEventListener("input", () => {
            this.data[key] = val.innerText;
          });
        }
        row.appendChild(val);
        return row;
      };

      info.appendChild(createRow("Signer", "signer"));
      info.appendChild(createRow("Issuer", "issuer"));
      info.appendChild(createRow("Date", "date"));

      container.appendChild(info);

      if (!this.readOnly) {
        const toggle = document.createElement("button");
        toggle.classList.add("doclib-cert-toggle");
        toggle.innerText = "Toggle Status";
        toggle.addEventListener("click", () => {
          this.data.valid = !this.data.valid;
          if (this.data.valid) container.classList.remove("invalid");
          else container.classList.add("invalid");
          renderContent();
        });
        container.appendChild(toggle);
      }
    };

    renderContent();

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
