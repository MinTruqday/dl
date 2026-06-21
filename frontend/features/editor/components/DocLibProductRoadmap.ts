import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibProductRoadmap implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Product Roadmap",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      q1: data?.q1 || ["DocLib Task 1"],
      q2: data?.q2 || ["DocLib Task 2"],
      q3: data?.q3 || ["DocLib Task 3"],
      q4: data?.q4 || ["DocLib Task 4"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-roadmap { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; font-family: sans-serif; overflow-x: auto; padding-bottom: 8px; }
      .doclib-rm-col { display: flex; flex-direction: column; gap: 8px; background: #f8fafc; border-radius: 8px; padding: 12px; border: 1px solid #e2e8f0; min-width: 200px; }
      .doclib-rm-header { font-size: 16px; font-weight: bold; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; margin-bottom: 8px; text-align: center; }
      .doclib-rm-item { background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px; font-size: 13px; color: #334155; position: relative; }
      .doclib-rm-item-text { outline: none; min-height: 20px; }
      .doclib-rm-item-text:empty:before { content: "DocLib Task..."; color: #94a3b8; }
      .doclib-rm-del { position: absolute; right: 4px; top: 4px; background: none; border: none; font-size: 10px; color: #ef4444; cursor: pointer; display: none; }
      .doclib-rm-item:hover .doclib-rm-del { display: block; }
      .doclib-rm-add { background: none; border: 1px dashed #cbd5e1; color: #64748b; padding: 8px; font-size: 12px; cursor: pointer; border-radius: 4px; text-align: center; }
      .doclib-rm-add:hover { background: #e2e8f0; }
    `;
    this.wrapper.appendChild(style);

    const roadmap = document.createElement("div");
    roadmap.classList.add("doclib-roadmap");

    const quarters = ["q1", "q2", "q3", "q4"];
    const titles = ["Q1", "Q2", "Q3", "Q4"];

    const renderUI = () => {
      roadmap.innerHTML = "";
      quarters.forEach((q, idx) => {
        const col = document.createElement("div");
        col.classList.add("doclib-rm-col");

        const header = document.createElement("div");
        header.classList.add("doclib-rm-header");
        header.innerText = titles[idx];
        col.appendChild(header);

        this.data[q].forEach((task: string, tIdx: number) => {
          const item = document.createElement("div");
          item.classList.add("doclib-rm-item");

          const text = document.createElement("div");
          text.classList.add("doclib-rm-item-text");
          text.innerText = task;
          if (!this.readOnly) {
            text.contentEditable = "true";
            text.addEventListener("input", () => { this.data[q][tIdx] = text.innerText; });

            const delBtn = document.createElement("button");
            delBtn.classList.add("doclib-rm-del");
            delBtn.innerText = "✕";
            delBtn.addEventListener("click", () => {
              this.data[q].splice(tIdx, 1);
              renderUI();
            });
            item.appendChild(delBtn);
          }
          item.appendChild(text);
          col.appendChild(item);
        });

        if (!this.readOnly) {
          const addBtn = document.createElement("button");
          addBtn.classList.add("doclib-rm-add");
          addBtn.innerText = "+ Add Task";
          addBtn.addEventListener("click", () => {
            this.data[q].push("");
            renderUI();
          });
          col.appendChild(addBtn);
        }

        roadmap.appendChild(col);
      });
    };

    renderUI();
    this.wrapper.appendChild(roadmap);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
