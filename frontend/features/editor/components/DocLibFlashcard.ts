import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFlashcard implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { front: string; back: string; hint: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Flashcard",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      front: data?.front || "",
      back: data?.back || "",
      hint: data?.hint || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-flashcard-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-flashcard-styles";
      style.innerHTML = `
        .doclib-fc-scene { perspective: 1000px; width: 100%; height: 200px; cursor: pointer; margin: 12px 0; }
        .doclib-fc-card { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; transition: transform 0.5s; }
        .doclib-fc-card.flipped { transform: rotateY(180deg); }
        .doclib-fc-face { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border: 1px solid #e2e8f0; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box; text-align: center; }
        .doclib-fc-front { background: #fff; }
        .doclib-fc-back { background: #0f172a; color: #fff; transform: rotateY(180deg); }
        .doclib-fc-question { font-size: 18px; font-weight: 600; color: #1e293b; }
        .doclib-fc-hint { font-size: 12px; color: #94a3b8; margin-top: 8px; }
        .doclib-fc-answer { font-size: 17px; font-weight: 500; }
        .doclib-fc-flip-label { font-size: 11px; color: #94a3b8; margin-top: 12px; }
        .doclib-fc-edit { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
        .doclib-fc-edit-field { display: flex; flex-direction: column; gap: 4px; }
        .doclib-fc-edit-field label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-fc-edit-field textarea { padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; resize: vertical; min-height: 60px; font-family: inherit; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const scene = document.createElement("div");
    scene.classList.add("doclib-fc-scene");

    const card = document.createElement("div");
    card.classList.add("doclib-fc-card");

    const front = document.createElement("div");
    front.classList.add("doclib-fc-face", "doclib-fc-front");

    const question = document.createElement("div");
    question.classList.add("doclib-fc-question");
    question.innerText = this.data.front;

    const hint = document.createElement("div");
    hint.classList.add("doclib-fc-hint");
    hint.innerText = this.data.hint ? ` ${this.data.hint}` : "";
    if (!this.data.hint) hint.style.display = "none";

    const flipLabel = document.createElement("div");
    flipLabel.classList.add("doclib-fc-flip-label");
    flipLabel.innerText = "Click to flip";

    front.appendChild(question);
    front.appendChild(hint);
    front.appendChild(flipLabel);

    const back = document.createElement("div");
    back.classList.add("doclib-fc-face", "doclib-fc-back");

    const answer = document.createElement("div");
    answer.classList.add("doclib-fc-answer");
    answer.innerText = this.data.back;

    back.appendChild(answer);
    card.appendChild(front);
    card.appendChild(back);
    scene.appendChild(card);

    scene.addEventListener("click", () => card.classList.toggle("flipped"));

    this.wrapper.appendChild(scene);

    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-fc-edit");

      const fields: { key: keyof typeof this.data; label: string }[] = [
        { key: "front", label: "Question" },
        { key: "back", label: "Answer" },
        { key: "hint", label: "Hint" },
      ];

      fields.forEach(({ key, label }) => {
        const field = document.createElement("div");
        field.classList.add("doclib-fc-edit-field");
        if (key === "hint") field.style.gridColumn = "1 / -1";

        const lbl = document.createElement("label");
        lbl.innerText = label;

        const textarea = document.createElement("textarea");
        textarea.value = this.data[key];
        textarea.addEventListener("input", () => {
          (this.data as any)[key] = textarea.value;
          if (key === "front") question.innerText = textarea.value;
          if (key === "back") answer.innerText = textarea.value;
          if (key === "hint") {
            hint.innerText = textarea.value ? ` ${textarea.value}` : "";
            hint.style.display = textarea.value ? "" : "none";
          }
        });

        field.appendChild(lbl);
        field.appendChild(textarea);
        editArea.appendChild(field);
      });

      this.wrapper.appendChild(editArea);
    }
  }

  save() {
    return this.data;
  }
}
