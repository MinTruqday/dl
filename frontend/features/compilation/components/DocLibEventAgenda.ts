import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibEventAgenda implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Event Agenda",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><line x1="8" y1="14" x2="16" y2="14"></line><line x1="8" y1="18" x2="12" y2="18"></line></svg>',
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
      events:
        data?.events && data.events.length > 0
          ? data.events
          : [{ time: "09:00 AM", title: "", speaker: "" }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-ea { font-family: sans-serif; max-width: 600px; margin: 16px auto; }
      .doclib-ea-title { font-size: 28px; font-weight: bold; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 24px; outline: none; }
      .doclib-ea-title:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-ea-list { display: flex; flex-direction: column; gap: 16px; }
      .doclib-ea-item { display: flex; gap: 16px; background: #f8fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; position: relative; }
      .doclib-ea-time { font-size: 14px; font-weight: bold; color: #3b82f6; width: 80px; flex-shrink: 0; outline: none; }
      .doclib-ea-time:empty:before { content: attr(data-placeholder); color: #93c5fd; }
      .doclib-ea-content { flex: 1; display: flex; flex-direction: column; gap: 4px; }
      .doclib-ea-etitle { font-size: 16px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-ea-etitle:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-ea-espeaker { font-size: 13px; color: #64748b; outline: none; }
      .doclib-ea-espeaker:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-ea-del { position: absolute; right: 12px; top: 12px; background: none; border: none; color: #ef4444; cursor: pointer; display: none; }
      .doclib-ea-item:hover .doclib-ea-del { display: block; }
      .doclib-ea-add { margin-top: 16px; width: 100%; padding: 12px; background: #e2e8f0; border: none; border-radius: 8px; font-weight: bold; color: #475569; cursor: pointer; }
      .doclib-ea-add:hover { background: #cbd5e1; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-ea");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-ea-title");
    titleEl.innerText = this.data.title;
    titleEl.dataset.placeholder = "DocLib Event Agenda";
    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      titleEl.addEventListener("input", () => {
        this.data.title = titleEl.innerText;
      });
    }
    container.appendChild(titleEl);

    const list = document.createElement("div");
    list.classList.add("doclib-ea-list");
    container.appendChild(list);

    const renderEvents = () => {
      list.innerHTML = "";
      this.data.events.forEach((ev: any, i: number) => {
        const item = document.createElement("div");
        item.classList.add("doclib-ea-item");

        const time = document.createElement("div");
        time.classList.add("doclib-ea-time");
        time.innerText = ev.time;
        time.dataset.placeholder = "00:00";

        const content = document.createElement("div");
        content.classList.add("doclib-ea-content");

        const eTitle = document.createElement("div");
        eTitle.classList.add("doclib-ea-etitle");
        eTitle.innerText = ev.title;
        eTitle.dataset.placeholder = "DocLib Session Title";

        const eSpeaker = document.createElement("div");
        eSpeaker.classList.add("doclib-ea-espeaker");
        eSpeaker.innerText = ev.speaker;
        eSpeaker.dataset.placeholder = "DocLib Speaker Name";

        if (!this.readOnly) {
          time.contentEditable = "true";
          time.addEventListener("input", () => {
            this.data.events[i].time = time.innerText;
          });
          eTitle.contentEditable = "true";
          eTitle.addEventListener("input", () => {
            this.data.events[i].title = eTitle.innerText;
          });
          eSpeaker.contentEditable = "true";
          eSpeaker.addEventListener("input", () => {
            this.data.events[i].speaker = eSpeaker.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-ea-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.events.splice(i, 1);
            renderEvents();
          });
          item.appendChild(del);
        }

        content.appendChild(eTitle);
        content.appendChild(eSpeaker);
        item.appendChild(time);
        item.appendChild(content);
        list.appendChild(item);
      });
    };

    renderEvents();

    if (!this.readOnly) {
      const add = document.createElement("button");
      add.classList.add("doclib-ea-add");
      add.innerText = "+ Add Session";
      add.addEventListener("click", () => {
        this.data.events.push({ time: "00:00", title: "", speaker: "" });
        renderEvents();
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
