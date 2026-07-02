import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormRadioButton implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form Radio Button",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="4"></circle></svg>',
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
      question: data?.question || "",
      options:
        data?.options && data.options.length > 0
          ? data.options
          : ["DocLib Option 1", "DocLib Option 2"],
      selectedIdx: data?.selectedIdx !== undefined ? data.selectedIdx : -1,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-radio { font-family: sans-serif; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px 0; max-width: 500px; }
      .doclib-radio-q { font-size: 16px; font-weight: bold; color: #0f172a; margin-bottom: 12px; outline: none; }
      .doclib-radio-q:empty:before { content: "DocLib Question"; color: #94a3b8; font-weight: normal; }
      .doclib-radio-opts { display: flex; flex-direction: column; gap: 8px; }
      .doclib-radio-opt { display: flex; align-items: center; gap: 8px; position: relative; }
      .doclib-radio-circle { width: 16px; height: 16px; border-radius: 50%; border: 2px solid #cbd5e1; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
      .doclib-radio-circle.selected { border-color: #3b82f6; }
      .doclib-radio-circle.selected::after { content: ""; width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; }
      .doclib-radio-text { flex: 1; font-size: 14px; color: #334155; outline: none; }
      .doclib-radio-text:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-radio-del { background: none; border: none; color: #ef4444; font-size: 12px; cursor: pointer; display: none; }
      .doclib-radio-opt:hover .doclib-radio-del { display: block; }
      .doclib-radio-add { margin-top: 12px; padding: 6px 12px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px; font-size: 13px; color: #64748b; cursor: pointer; display: inline-block; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-radio");

    const qEl = document.createElement("div");
    qEl.classList.add("doclib-radio-q");
    qEl.innerText = this.data.question;
    if (!this.readOnly) {
      qEl.contentEditable = "true";
      qEl.addEventListener("input", () => {
        this.data.question = qEl.innerText;
      });
    }
    container.appendChild(qEl);

    const optsCont = document.createElement("div");
    optsCont.classList.add("doclib-radio-opts");
    container.appendChild(optsCont);

    const renderOpts = () => {
      optsCont.innerHTML = "";
      this.data.options.forEach((opt: string, i: number) => {
        const optEl = document.createElement("div");
        optEl.classList.add("doclib-radio-opt");

        const circle = document.createElement("div");
        circle.classList.add("doclib-radio-circle");
        if (this.data.selectedIdx === i) circle.classList.add("selected");
        circle.addEventListener("click", () => {
          this.data.selectedIdx = i;
          renderOpts();
        });

        const text = document.createElement("div");
        text.classList.add("doclib-radio-text");
        text.innerText = opt;
        text.dataset.placeholder = "DocLib Option";
        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", () => {
            this.data.options[i] = text.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-radio-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.options.splice(i, 1);
            if (this.data.selectedIdx === i) this.data.selectedIdx = -1;
            else if (this.data.selectedIdx > i) this.data.selectedIdx--;
            renderOpts();
          });

          optEl.appendChild(circle);
          optEl.appendChild(text);
          optEl.appendChild(del);
        } else {
          optEl.appendChild(circle);
          optEl.appendChild(text);
        }

        optsCont.appendChild(optEl);
      });
    };

    renderOpts();

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-radio-add");
      addBtn.innerText = "+ Add Option";
      addBtn.addEventListener("click", () => {
        this.data.options.push("");
        renderOpts();
      });
      container.appendChild(addBtn);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
