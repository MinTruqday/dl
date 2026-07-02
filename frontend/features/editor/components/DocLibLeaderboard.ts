import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibLeaderboard implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Leaderboard",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>',
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
      title: data?.title || "",
      players:
        data?.players && data.players.length > 0
          ? data.players
          : [
              { name: "", score: "" },
              { name: "", score: "" },
            ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-lb { font-family: sans-serif; max-width: 500px; margin: 16px auto; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
      .doclib-lb-title { font-size: 24px; font-weight: 900; color: #1e293b; text-align: center; text-transform: uppercase; margin-bottom: 24px; outline: none; }
      .doclib-lb-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-lb-list { display: flex; flex-direction: column; gap: 8px; }
      .doclib-lb-row { display: flex; align-items: center; padding: 12px 16px; background: #f8fafc; border-radius: 6px; position: relative; }
      .doclib-lb-row:nth-child(1) { background: #fef08a; }
      .doclib-lb-row:nth-child(2) { background: #e2e8f0; }
      .doclib-lb-row:nth-child(3) { background: #fed7aa; }
      .doclib-lb-rank { font-size: 18px; font-weight: bold; color: #475569; width: 40px; }
      .doclib-lb-row:nth-child(1) .doclib-lb-rank { color: #ca8a04; }
      .doclib-lb-name { flex: 1; font-size: 16px; font-weight: bold; color: #0f172a; outline: none; }
      .doclib-lb-name:empty:before { content: attr(data-placeholder); color: rgba(15,23,42,0.4); }
      .doclib-lb-score { font-size: 18px; font-weight: 900; color: #3b82f6; outline: none; }
      .doclib-lb-score:empty:before { content: attr(data-placeholder); color: rgba(59,130,246,0.4); }
      .doclib-lb-del { position: absolute; right: -24px; top: 14px; background: none; border: none; color: #ef4444; cursor: pointer; display: none; }
      .doclib-lb-row:hover .doclib-lb-del { display: block; }
      .doclib-lb-add { margin-top: 16px; width: 100%; padding: 12px; border: 1px dashed #cbd5e1; border-radius: 6px; background: none; color: #64748b; font-weight: bold; cursor: pointer; }
      .doclib-lb-add:hover { background: #f8fafc; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-lb");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-lb-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Leaderboard";
    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => {
        this.data.title = titleEl.innerText;
      });
    }
    container.appendChild(titleEl);

    const list = document.createElement("div");
    list.classList.add("doclib-lb-list");
    container.appendChild(list);

    const renderRows = () => {
      list.innerHTML = "";
      this.data.players.forEach((p: any, i: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-lb-row");

        const rank = document.createElement("div");
        rank.classList.add("doclib-lb-rank");
        rank.innerText = `#${i + 1}`;

        const name = document.createElement("div");
        name.classList.add("doclib-lb-name");
        name.innerText = p.name;
        name.dataset.placeholder = "DocLib Player";

        const score = document.createElement("div");
        score.classList.add("doclib-lb-score");
        score.innerText = p.score;
        score.dataset.placeholder = "0";

        if (!this.readOnly) {
          name.contentEditable = "true";
          name.addEventListener("input", () => {
            this.data.players[i].name = name.innerText;
          });
          score.contentEditable = "true";
          score.addEventListener("input", () => {
            this.data.players[i].score = score.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-lb-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.players.splice(i, 1);
            renderRows();
          });
          row.appendChild(del);
        }

        row.appendChild(rank);
        row.appendChild(name);
        row.appendChild(score);
        list.appendChild(row);
      });
    };

    renderRows();

    if (!this.readOnly) {
      const add = document.createElement("button");
      add.classList.add("doclib-lb-add");
      add.innerText = "+ Add Player";
      add.addEventListener("click", () => {
        this.data.players.push({ name: "", score: "" });
        renderRows();
      });
      container.appendChild(add);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
