import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDropCap implements BlockTool {
  static readonly feature = {
    id: "DocLibDropCap",
    title: "DocLib Drop Cap",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba8d39bd3278083d"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="20,9 10,6 20,5 12,14 4,4 20,16"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Drop Cap",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ba8d39bd3278083d"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="20,9 10,6 20,5 12,14 4,4 20,16"/></svg>',
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
      letter: data?.letter || "",
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-dropcap { display: flex; gap: 8px; margin: 16px 0; }
      .doclib-dropcap-letter { font-size: 64px; font-weight: 700; line-height: 0.8; color: #1e293b; float: left; margin-right: 8px; margin-bottom: -8px; margin-top: 8px; font-family: Georgia, serif; min-width: 48px; text-align: center; }
      .doclib-dropcap-text { font-size: 16px; line-height: 1.6; color: #334155; flex: 1; }
      .doclib-dropcap-input-letter { width: 64px; font-size: 48px; text-align: center; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; outline: none; }
      .doclib-dropcap-input-text { flex: 1; min-height: 120px; border: 1px solid #cbd5e1; border-radius: 4px; padding: 12px; font-size: 15px; outline: none; resize: vertical; }
      .doclib-dropcap-edit { display: flex; gap: 16px; align-items: flex-start; background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px dashed #cbd5e1; }
    `;
    this.wrapper.appendChild(style);

    if (this.readOnly) {
      const container = document.createElement("div");
      container.classList.add("doclib-dropcap");

      const letter = document.createElement("div");
      letter.classList.add("doclib-dropcap-letter");
      letter.innerText = this.data.letter;

      const text = document.createElement("div");
      text.classList.add("doclib-dropcap-text");
      text.innerText = this.data.text;

      container.appendChild(letter);
      container.appendChild(text);
      this.wrapper.appendChild(container);
      return this.wrapper;
    }

    const edit = document.createElement("div");
    edit.classList.add("doclib-dropcap-edit");

    const inputLetter = document.createElement("input");
    inputLetter.classList.add("doclib-dropcap-input-letter");
    inputLetter.maxLength = 1;
    inputLetter.placeholder = "DocLib Input";
    inputLetter.value = this.data.letter;
    inputLetter.addEventListener("input", () => {
      this.data.letter = inputLetter.value.charAt(0);
    });

    const inputText = document.createElement("textarea");
    inputText.classList.add("doclib-dropcap-input-text");
    inputText.placeholder = "DocLib Text";
    inputText.value = this.data.text;
    inputText.addEventListener("input", () => {
      this.data.text = inputText.value;
    });

    edit.appendChild(inputLetter);
    edit.appendChild(inputText);
    this.wrapper.appendChild(edit);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      letter: this.data.letter,
      text: this.data.text,
    };
  }
}
