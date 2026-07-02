import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFeedback implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    question: string;
    reactions: { emoji: string; label: string; count: number }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Feedback",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>',
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
      reactions: data?.reactions || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-fb-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-fb-styles";
      style.innerHTML = `
        .doclib-fb-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; background: #fff; margin: 12px 0; text-align: center; }
        .doclib-fb-question { font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 20px; }
        .doclib-fb-reactions { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
        .doclib-fb-reaction { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 12px; cursor: pointer; transition: all 0.15s; min-width: 72px; background: #fff; }
        .doclib-fb-reaction:hover { border-color: #0284c7; background: #f0f9ff; transform: translateY(-2px); }
        .doclib-fb-reaction.selected { border-color: #0284c7; background: #f0f9ff; }
        .doclib-fb-emoji { font-size: 28px; line-height: 1; }
        .doclib-fb-label { font-size: 11px; font-weight: 500; color: #64748b; }
        .doclib-fb-count { font-size: 13px; font-weight: 700; color: #0284c7; }
        .doclib-fb-thanks { margin-top: 16px; font-size: 13px; color: #059669; font-weight: 500; display: none; }
        .doclib-fb-edit { border-top: 1px solid #f1f5f9; margin-top: 16px; padding-top: 14px; }
        .doclib-fb-q-input { width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; box-sizing: border-box; margin-bottom: 10px; }
        .doclib-fb-react-row { display: flex; gap: 8px; align-items: center; margin-bottom: 5px; }
        .doclib-fb-react-input { padding: 5px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; }
        .doclib-fb-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
        .doclib-fb-add-btn { padding: 5px 10px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 11px; cursor: pointer; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-fb-wrapper");

    const question = document.createElement("div");
    question.classList.add("doclib-fb-question");
    question.innerText = this.data.question;

    const reactionsRow = document.createElement("div");
    reactionsRow.classList.add("doclib-fb-reactions");

    const thanks = document.createElement("div");
    thanks.classList.add("doclib-fb-thanks");
    thanks.innerText = "Thanks for your feedback";

    let voted = false;

    this.data.reactions.forEach((reaction, idx) => {
      const btn = document.createElement("div");
      btn.classList.add("doclib-fb-reaction");

      const emoji = document.createElement("div");
      emoji.classList.add("doclib-fb-emoji");
      emoji.innerText = reaction.emoji;

      const label = document.createElement("div");
      label.classList.add("doclib-fb-label");
      label.innerText = reaction.label;

      const count = document.createElement("div");
      count.classList.add("doclib-fb-count");
      count.innerText = reaction.count > 0 ? `${reaction.count}` : "";

      btn.appendChild(emoji);
      btn.appendChild(label);
      btn.appendChild(count);

      btn.addEventListener("click", () => {
        if (voted) return;
        voted = true;
        reaction.count++;
        count.innerText = `${reaction.count}`;
        btn.classList.add("selected");
        thanks.style.display = "block";
      });

      reactionsRow.appendChild(btn);
    });

    this.wrapper.appendChild(question);
    this.wrapper.appendChild(reactionsRow);
    this.wrapper.appendChild(thanks);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-fb-edit");

      const qInput = document.createElement("input");
      qInput.classList.add("doclib-fb-q-input");
      qInput.value = this.data.question;
      qInput.placeholder = "DocLib Question";
      qInput.addEventListener("input", () => {
        this.data.question = qInput.value;
        question.innerText = qInput.value;
      });

      edit.appendChild(qInput);

      const reactRows = document.createElement("div");

      const renderReactRows = () => {
        reactRows.innerHTML = "";
        this.data.reactions.forEach((r, i) => {
          const row = document.createElement("div");
          row.classList.add("doclib-fb-react-row");

          const emojiIn = document.createElement("input");
          emojiIn.classList.add("doclib-fb-react-input");
          emojiIn.style.width = "48px";
          emojiIn.style.textAlign = "center";
          emojiIn.value = r.emoji;
          emojiIn.addEventListener("input", () => {
            r.emoji = emojiIn.value;
            this.buildUI();
          });

          const labelIn = document.createElement("input");
          labelIn.classList.add("doclib-fb-react-input");
          labelIn.style.flex = "1";
          labelIn.value = r.label;
          labelIn.addEventListener("input", () => {
            r.label = labelIn.value;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-fb-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.reactions.splice(i, 1);
            this.buildUI();
          });

          row.appendChild(emojiIn);
          row.appendChild(labelIn);
          row.appendChild(del);
          reactRows.appendChild(row);
        });

        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-fb-add-btn");
        addBtn.innerText = "Add reaction";
        addBtn.addEventListener("click", () => {
          this.data.reactions.push({ emoji: "", label: "New", count: 0 });
          this.buildUI();
        });
        reactRows.appendChild(addBtn);
      };

      renderReactRows();
      edit.appendChild(reactRows);
      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
