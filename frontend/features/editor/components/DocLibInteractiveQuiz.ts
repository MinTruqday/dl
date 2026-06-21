import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibInteractiveQuiz implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    question: string;
    options: { text: string; isCorrect: boolean }[];
    explanation: string;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Quiz",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      question: data?.question || "What is the capital of France",
      options: data?.options && data.options.length > 0 ? data.options : [
        { text: "London", isCorrect: false },
        { text: "Berlin", isCorrect: false },
        { text: "Paris", isCorrect: true },
        { text: "Madrid", isCorrect: false },
      ],
      explanation: data?.explanation || "Paris is the capital and most populous city of France",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-quiz-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-quiz-styles";
      style.innerHTML = `
        .doclib-qz-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; background: #fff; margin: 16px 0; font-family: sans-serif; }
        .doclib-qz-q { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 20px; line-height: 1.4; }
        .doclib-qz-opts { display: flex; flex-direction: column; gap: 10px; }
        .doclib-qz-opt { display: flex; align-items: center; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 15px; color: #334155; font-weight: 500; background: #fff; }
        .doclib-qz-opt:hover { border-color: #cbd5e1; background: #f8fafc; }
        .doclib-qz-opt.selected { border-color: #3b82f6; background: #eff6ff; }
        .doclib-qz-opt.correct { border-color: #10b981; background: #ecfdf5; color: #065f46; }
        .doclib-qz-opt.incorrect { border-color: #ef4444; background: #fef2f2; color: #991b1b; }
        .doclib-qz-opt-icon { margin-left: auto; font-size: 18px; display: none; }
        .doclib-qz-opt.correct .doclib-qz-opt-icon, .doclib-qz-opt.incorrect .doclib-qz-opt-icon { display: block; }
        .doclib-qz-expl { margin-top: 20px; padding: 16px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; font-size: 14px; color: #166534; line-height: 1.5; display: none; }
        .doclib-qz-expl.show { display: block; animation: qz-fade-in 0.3s; }
        @keyframes qz-fade-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        
        .doclib-qz-edit { border-top: 1px solid #e2e8f0; margin-top: 24px; padding-top: 20px; }
        .doclib-qz-input { width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; outline: none; margin-bottom: 12px; font-family: inherit; }
        .doclib-qz-edit-opt { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
        .doclib-qz-edit-cb { width: 18px; height: 18px; cursor: pointer; }
        .doclib-qz-del { background: none; border: none; color: #ef4444; font-size: 20px; cursor: pointer; padding: 0 4px; }
        .doclib-qz-add { padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 12px; cursor: pointer; margin-top: 4px; font-weight: 500; }
        .doclib-qz-label { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 6px; display: block; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-qz-wrapper");

    let answered = false;

    const qTitle = document.createElement("div");
    qTitle.classList.add("doclib-qz-q");
    qTitle.innerText = this.data.question;
    this.wrapper.appendChild(qTitle);

    const optsContainer = document.createElement("div");
    optsContainer.classList.add("doclib-qz-opts");

    const explanation = document.createElement("div");
    explanation.classList.add("doclib-qz-expl");
    explanation.innerHTML = `<strong>Explanation:</strong><br>${this.data.explanation}`;

    const optElements: HTMLElement[] = [];

    this.data.options.forEach((opt, idx) => {
      const el = document.createElement("div");
      el.classList.add("doclib-qz-opt");
      
      const text = document.createElement("span");
      text.innerText = opt.text;
      
      const icon = document.createElement("span");
      icon.classList.add("doclib-qz-opt-icon");
      icon.innerText = opt.isCorrect ? "v" : "x";

      el.appendChild(text);
      el.appendChild(icon);
      
      el.addEventListener("click", () => {
        if (answered || this.readOnly === false) return; // Only interactive in readonly/view mode
        answered = true;
        
        optElements.forEach((oEl, i) => {
          oEl.style.cursor = "default";
          if (this.data.options[i].isCorrect) {
            oEl.classList.add("correct");
          }
        });

        if (!opt.isCorrect) {
          el.classList.add("incorrect");
        }

        if (this.data.explanation) {
          explanation.classList.add("show");
        }
      });

      optElements.push(el);
      optsContainer.appendChild(el);
    });

    this.wrapper.appendChild(optsContainer);
    this.wrapper.appendChild(explanation);

    // Edit Mode UI
    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-qz-edit");

      const qLabel = document.createElement("label");
      qLabel.classList.add("doclib-qz-label");
      qLabel.innerText = "Question";
      editArea.appendChild(qLabel);

      const qInput = document.createElement("input");
      qInput.classList.add("doclib-qz-input");
      qInput.value = this.data.question;
      qInput.addEventListener("input", () => { this.data.question = qInput.value; qTitle.innerText = this.data.question; });
      editArea.appendChild(qInput);

      const optLabel = document.createElement("label");
      optLabel.classList.add("doclib-qz-label");
      optLabel.innerText = "Options";
      optLabel.style.marginTop = "16px";
      editArea.appendChild(optLabel);

      const optsEditArea = document.createElement("div");
      
      const renderOptsEdit = () => {
        optsEditArea.innerHTML = "";
        this.data.options.forEach((opt, idx) => {
          const row = document.createElement("div");
          row.classList.add("doclib-qz-edit-opt");

          const cb = document.createElement("input");
          cb.type = "radio";
          cb.name = "doclib-qz-correct-" + this.mkId(); // Group them
          cb.classList.add("doclib-qz-edit-cb");
          cb.checked = opt.isCorrect;
          cb.addEventListener("change", () => {
            this.data.options.forEach(o => o.isCorrect = false);
            opt.isCorrect = true;
          });

          const inp = document.createElement("input");
          inp.classList.add("doclib-qz-input");
          inp.style.marginBottom = "0";
          inp.value = opt.text;
          inp.addEventListener("input", () => opt.text = inp.value);

          const del = document.createElement("button");
          del.classList.add("doclib-qz-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.options.splice(idx, 1);
            if (opt.isCorrect && this.data.options.length > 0) {
              this.data.options[0].isCorrect = true; // ensure at least one is true if deleted
            }
            this.buildUI();
          });

          row.appendChild(cb);
          row.appendChild(inp);
          row.appendChild(del);
          optsEditArea.appendChild(row);
        });

        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-qz-add");
        addBtn.innerText = "Add Option";
        addBtn.addEventListener("click", () => {
          this.data.options.push({ text: "New Option", isCorrect: this.data.options.length === 0 });
          this.buildUI();
        });
        optsEditArea.appendChild(addBtn);
      };

      renderOptsEdit();
      editArea.appendChild(optsEditArea);

      const expLabel = document.createElement("label");
      expLabel.classList.add("doclib-qz-label");
      expLabel.innerText = "Explanation";
      expLabel.style.marginTop = "16px";
      editArea.appendChild(expLabel);

      const expInput = document.createElement("textarea");
      expInput.classList.add("doclib-qz-input");
      expInput.style.resize = "vertical";
      expInput.style.minHeight = "60px";
      expInput.value = this.data.explanation;
      expInput.addEventListener("input", () => this.data.explanation = expInput.value);
      editArea.appendChild(expInput);

      this.wrapper.appendChild(editArea);
    }
  }

  private mkId() {
    return Math.random().toString(36).substr(2, 9);
  }

  save() {
    return this.data;
  }
}
