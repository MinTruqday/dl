import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibQuiz implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    question: string;
    answers: { text: string; isCorrect: boolean }[];
  };

  static get toolbox() {
    return {
      title: "DocLib Quiz",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      question: data.question || "",
      answers:
        data.answers && data.answers.length > 0
          ? data.answers
          : [
              { text: "", isCorrect: false },
              { text: "", isCorrect: false },
            ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-quiz-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-quiz-styles";
      style.innerHTML = `
            .doclib-quiz-wrapper { padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; margin: 16px 0; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); }
            .doclib-quiz-question { font-weight: 700; font-size: 1.1em; margin-bottom: 16px; outline: none; }
            .doclib-quiz-question:empty::before { content: 'Enter quiz question'; color: #94a3b8; pointer-events: none; }
            .doclib-quiz-answers { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
            .doclib-quiz-answer { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; transition: all 0.2s; }
            .doclib-quiz-answer:hover { border-color: #cbd5e1; }
            .doclib-quiz-answer.correct { border-color: #22c55e; background: #f0fdf4; }
            .doclib-quiz-radio { width: 18px; height: 18px; cursor: pointer; accent-color: #22c55e; }
            .doclib-quiz-text { flex-grow: 1; outline: none; font-size: 0.95em; }
            .doclib-quiz-text:empty::before { content: 'Enter answer'; color: #94a3b8; pointer-events: none; }
            .doclib-quiz-add { color: #3b82f6; cursor: pointer; font-size: 0.9em; font-weight: 500; display: inline-block; padding: 4px 8px; border-radius: 4px; }
            .doclib-quiz-add:hover { background: #eff6ff; }
            .doclib-quiz-remove { color: #ef4444; cursor: pointer; padding: 4px; opacity: 0.5; transition: opacity 0.2s; }
            .doclib-quiz-answer:hover .doclib-quiz-remove { opacity: 1; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-quiz-wrapper");

    const q = document.createElement("div");
    q.classList.add("doclib-quiz-question");
    q.contentEditable = "true";
    q.innerHTML = this.data.question;
    q.addEventListener("input", () => (this.data.question = q.innerHTML));
    container.appendChild(q);

    const answersDiv = document.createElement("div");
    answersDiv.classList.add("doclib-quiz-answers");

    this.data.answers.forEach((ans, i) => {
      const aDiv = document.createElement("div");
      aDiv.classList.add("doclib-quiz-answer");
      if (ans.isCorrect) aDiv.classList.add("correct");

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = `quiz-${Math.floor(Math.random() * 10000)}`;
      radio.checked = ans.isCorrect;
      radio.classList.add("doclib-quiz-radio");
      radio.addEventListener("change", () => {
        this.data.answers.forEach((a) => (a.isCorrect = false));
        ans.isCorrect = true;
        this.buildUI();
      });

      const text = document.createElement("div");
      text.classList.add("doclib-quiz-text");
      text.contentEditable = "true";
      text.innerHTML = ans.text;
      text.addEventListener("input", () => (ans.text = text.innerHTML));

      const rmBtn = document.createElement("div");
      rmBtn.classList.add("doclib-quiz-remove");
      rmBtn.innerHTML =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
      rmBtn.addEventListener("click", () => {
        if (this.data.answers.length > 2) {
          this.data.answers.splice(i, 1);
          this.buildUI();
        }
      });

      aDiv.appendChild(radio);
      aDiv.appendChild(text);
      aDiv.appendChild(rmBtn);
      answersDiv.appendChild(aDiv);
    });

    container.appendChild(answersDiv);

    const addBtn = document.createElement("div");
    addBtn.classList.add("doclib-quiz-add");
    addBtn.innerText = "+ Add answer";
    addBtn.addEventListener("click", () => {
      this.data.answers.push({ text: "", isCorrect: false });
      this.buildUI();
    });

    container.appendChild(addBtn);
    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
