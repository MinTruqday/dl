import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibWordCloud implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { words: { text: string; weight: number }[] };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Word Cloud",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      words: data?.words || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-wc-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-wc-styles";
      style.innerHTML = `
        .doclib-wc-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; background: #fff; margin: 12px 0; }
        .doclib-wc-cloud { display: flex; flex-wrap: wrap; gap: 10px 16px; justify-content: center; align-items: center; min-height: 120px; padding: 12px; }
        .doclib-wc-word { cursor: pointer; font-weight: 600; border-radius: 4px; padding: 2px 4px; transition: opacity 0.15s; user-select: none; }
        .doclib-wc-word:hover { opacity: 0.75; }
        .doclib-wc-controls { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; align-items: center; border-top: 1px solid #e2e8f0; padding-top: 12px; }
        .doclib-wc-new-input { flex: 1; min-width: 120px; padding: 7px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; }
        .doclib-wc-add-btn { padding: 7px 14px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private getColor(weight: number): string {
    const colors = ["#94a3b8", "#64748b", "#0284c7", "#0369a1", "#0c4a6e"];
    return colors[Math.min(weight - 1, colors.length - 1)];
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-wc-wrapper");

    const cloud = document.createElement("div");
    cloud.classList.add("doclib-wc-cloud");

    const maxWeight = Math.max(this.data.words.map((w) => w.weight), 1);

    this.data.words.forEach((word, idx) => {
      const span = document.createElement("span");
      span.classList.add("doclib-wc-word");
      span.innerText = word.text;
      const fontSize = 12 + (word.weight / maxWeight) * 26;
      span.style.fontSize = `${fontSize}px`;
      span.style.color = this.getColor(word.weight);

      if (!this.readOnly) {
        span.title = `Weight: ${word.weight} — Click to increase, Shift+Click to decrease`;
        span.addEventListener("click", (e) => {
          if (e.shiftKey) {
            word.weight = Math.max(1, word.weight - 1);
          } else {
            word.weight = Math.min(5, word.weight + 1);
          }
          this.buildUI();
        });
        span.addEventListener("dblclick", (e) => {
          e.stopPropagation();
          this.data.words.splice(idx, 1);
          this.buildUI();
        });
      }

      cloud.appendChild(span);
    });

    this.wrapper.appendChild(cloud);

    if (!this.readOnly) {
      const hint = document.createElement("div");
      hint.style.cssText = "font-size:11px;color:#94a3b8;text-align:center;margin-top:8px;";
      hint.innerText = "Click = increase weight    Shift+Click = decrease    Double-click = remove";
      this.wrapper.appendChild(hint);

      const controls = document.createElement("div");
      controls.classList.add("doclib-wc-controls");

      const input = document.createElement("input");
      input.classList.add("doclib-wc-new-input");
      input.placeholder = "Add new word";

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-wc-add-btn");
      addBtn.innerText = "Add word";

      const addWord = () => {
        const text = input.value.trim();
        if (text && !this.data.words.find((w) => w.text === text)) {
          this.data.words.push({ text, weight: 2 });
          input.value = "";
          this.buildUI();
        }
      };

      addBtn.addEventListener("click", addWord);
      input.addEventListener("keydown", (e) => { if (e.key === "Enter") addWord(); });

      controls.appendChild(input);
      controls.appendChild(addBtn);
      this.wrapper.appendChild(controls);
    }
  }

  save() {
    return this.data;
  }
}
