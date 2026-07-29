import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPrintPreview implements BlockTool {
  static readonly feature = {
    id: "DocLibPrintPreview",
    title: "Print Preview",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="af50107b948d0df5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="9,16 20,8 16,9 17,11 8,16 15,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Print Preview",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="af50107b948d0df5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="9,16 20,8 16,9 17,11 8,16 15,4"/></svg>',
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
      orientation: data?.orientation || "Portrait",
      paperSize: data?.paperSize || "A4",
      margins: data?.margins || "Normal",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-print { display: flex; gap: 24px; padding: 24px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; margin: 16px 0; max-width: 600px; font-family: sans-serif; }
      .doclib-print-settings { flex: 1; display: flex; flex-direction: column; gap: 16px; }
      .doclib-print-title { font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 8px; }
      .doclib-print-field { display: flex; flex-direction: column; gap: 4px; }
      .doclib-print-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; }
      .doclib-print-select { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: #fff; outline: none; font-size: 14px; }
      .doclib-print-preview { width: 150px; display: flex; align-items: center; justify-content: center; border-left: 1px dashed #cbd5e1; padding-left: 24px; }
      .doclib-print-paper { background: #fff; border: 1px solid #94a3b8; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); transition: all 0.3s ease; position: relative; }
      .doclib-print-paper::after { content: "DocLib Print"; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #cbd5e1; font-size: 10px; font-weight: bold; text-transform: uppercase; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-print");

    const settings = document.createElement("div");
    settings.classList.add("doclib-print-settings");

    const title = document.createElement("div");
    title.classList.add("doclib-print-title");
    title.innerText = "Print Settings";
    settings.appendChild(title);

    const createField = (label: string, key: string, options: string[]) => {
      const field = document.createElement("div");
      field.classList.add("doclib-print-field");

      const lbl = document.createElement("div");
      lbl.classList.add("doclib-print-label");
      lbl.innerText = label;

      const sel = document.createElement("select");
      sel.classList.add("doclib-print-select");
      if (this.readOnly) sel.disabled = true;

      options.forEach((opt) => {
        const option = document.createElement("option");
        option.value = opt;
        option.innerText = opt;
        if (this.data[key] === opt) option.selected = true;
        sel.appendChild(option);
      });

      if (!this.readOnly) {
        sel.addEventListener("change", () => {
          this.data[key] = sel.value;
          updatePreview();
        });
      }

      field.appendChild(lbl);
      field.appendChild(sel);
      return field;
    };

    settings.appendChild(
      createField("Orientation", "orientation", ["Portrait", "Landscape"]),
    );
    settings.appendChild(
      createField("Paper Size", "paperSize", [
        "A4",
        "Letter",
        "Legal",
        "Executive",
      ]),
    );
    settings.appendChild(
      createField("Margins", "margins", [
        "Normal",
        "Narrow",
        "Moderate",
        "Wide",
      ]),
    );
    container.appendChild(settings);

    const previewCont = document.createElement("div");
    previewCont.classList.add("doclib-print-preview");

    const paper = document.createElement("div");
    paper.classList.add("doclib-print-paper");
    previewCont.appendChild(paper);
    container.appendChild(previewCont);

    const updatePreview = () => {
      let width = 80;
      let height = 113;

      if (this.data.paperSize === "Letter") {
        height = 104;
      } else if (this.data.paperSize === "Legal") {
        height = 138;
      }

      if (this.data.orientation === "Landscape") {
        const temp = width;
        width = height;
        height = temp;
      }

      paper.style.width = width + "px";
      paper.style.height = height + "px";

      let padding = "10px";
      if (this.data.margins === "Narrow") padding = "5px";
      if (this.data.margins === "Wide") padding = "20px";

      paper.style.boxSizing = "border-box";
      paper.style.borderWidth = padding;
      paper.style.borderStyle = "solid";
      paper.style.borderColor = "transparent";
      paper.style.backgroundClip = "content-box";
      paper.style.backgroundColor = "#e2e8f0";
      paper.style.boxShadow =
        "0 0 0 1px #94a3b8 inset, 0 4px 6px -1px rgba(0,0,0,0.1)";
    };

    updatePreview();

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
