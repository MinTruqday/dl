import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibGreetingLine implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Greeting Line",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>',
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
      greeting: data?.greeting || "Dear",
      format: data?.format || "Mr. Randall",
      punctuation: data?.punctuation || ",",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-gl { font-family: "Times New Roman", serif; font-size: 16px; margin: 16px 0; }
      .doclib-gl-editor { display: flex; gap: 8px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; font-family: sans-serif; font-size: 14px; margin-bottom: 8px; }
      .doclib-gl-select { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; background: #fff; }
      .doclib-gl-preview { font-style: italic; color: #475569; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");

    if (!this.readOnly) {
      const editor = document.createElement("div");
      editor.classList.add("doclib-gl-editor");

      const gSel = document.createElement("select");
      gSel.classList.add("doclib-gl-select");
      ["Dear", "To", "None"].forEach((v) => {
        const o = document.createElement("option");
        o.value = v;
        o.innerText = v;
        if (this.data.greeting === v) o.selected = true;
        gSel.appendChild(o);
      });

      const fSel = document.createElement("select");
      fSel.classList.add("doclib-gl-select");
      [
        "Mr. Randall",
        "Joshua",
        "Joshua Randall Jr.",
        "Mr. Joshua Randall Jr.",
      ].forEach((v) => {
        const o = document.createElement("option");
        o.value = v;
        o.innerText = v;
        if (this.data.format === v) o.selected = true;
        fSel.appendChild(o);
      });

      const pSel = document.createElement("select");
      pSel.classList.add("doclib-gl-select");
      [",", ":", "None"].forEach((v) => {
        const o = document.createElement("option");
        o.value = v;
        o.innerText = v;
        if (this.data.punctuation === v) o.selected = true;
        pSel.appendChild(o);
      });

      editor.appendChild(gSel);
      editor.appendChild(fSel);
      editor.appendChild(pSel);
      container.appendChild(editor);

      const updateData = () => {
        this.data.greeting = gSel.value;
        this.data.format = fSel.value;
        this.data.punctuation = pSel.value;
        renderPreview();
      };
      gSel.addEventListener("change", updateData);
      fSel.addEventListener("change", updateData);
      pSel.addEventListener("change", updateData);
    }

    const preview = document.createElement("div");
    preview.classList.add("doclib-gl");
    container.appendChild(preview);

    const renderPreview = () => {
      let text = "";
      if (this.data.greeting !== "None") text += this.data.greeting + " ";
      text += `«DocLib ${this.data.format}»`;
      if (this.data.punctuation !== "None") text += this.data.punctuation;
      preview.innerText = text;
    };

    renderPreview();
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
