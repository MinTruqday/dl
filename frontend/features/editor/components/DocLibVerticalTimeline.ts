import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibVerticalTimeline implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    events: { id: string; date: string; title: string; description: string; color: string }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Vertical Timeline",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  private mkId() { return Math.random().toString(36).substring(2, 8); }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      events: data?.events && data.events.length > 0 ? data.events : [
        { id: this.mkId(), date: "Jan 2024", title: "Project Start", description: "Initial kickoff and planning phase", color: "#3b82f6" },
        { id: this.mkId(), date: "Mar 2024", title: "Beta Release", description: "First public beta available to testers", color: "#10b981" },
        { id: this.mkId(), date: "Jun 2024", title: "Version 1.0", description: "Official production release", color: "#8b5cf6" },
      ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-timeline-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-timeline-styles";
      style.innerHTML = `
        .doclib-tl-wrapper { padding: 20px 0; margin: 12px 0; font-family: sans-serif; position: relative; }
        .doclib-tl-wrapper::before { content: ''; position: absolute; left: 50%; top: 20px; bottom: 20px; width: 2px; background: #e2e8f0; transform: translateX(-50%); }
        .doclib-tl-event { display: flex; justify-content: center; align-items: center; margin-bottom: 30px; position: relative; width: 100%; }
        .doclib-tl-event:nth-child(odd) { flex-direction: row-reverse; }
        .doclib-tl-content { width: 45%; padding: 16px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); position: relative; }
        .doclib-tl-date { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
        .doclib-tl-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        .doclib-tl-desc { font-size: 14px; color: #475569; line-height: 1.5; }
        .doclib-tl-dot { width: 16px; height: 16px; border-radius: 50%; border: 3px solid #fff; position: absolute; left: 50%; transform: translateX(-50%); z-index: 1; box-shadow: 0 0 0 2px #e2e8f0; }
        .doclib-tl-edit { border-top: 1px solid #e2e8f0; margin-top: 24px; padding-top: 16px; display: flex; flex-direction: column; gap: 8px; }
        .doclib-tl-edit-row { display: grid; grid-template-columns: 1fr 2fr 3fr 40px 30px; gap: 8px; align-items: center; }
        .doclib-tl-input { padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; width: 100%; box-sizing: border-box; }
        .doclib-tl-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
        .doclib-tl-add-btn { align-self: flex-start; padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; cursor: pointer; margin-top: 8px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-tl-wrapper");

    this.data.events.forEach((event, idx) => {
      const el = document.createElement("div");
      el.classList.add("doclib-tl-event");

      const content = document.createElement("div");
      content.classList.add("doclib-tl-content");

      const date = document.createElement("div");
      date.classList.add("doclib-tl-date");
      date.style.color = event.color;
      date.innerText = event.date;

      const title = document.createElement("div");
      title.classList.add("doclib-tl-title");
      title.innerText = event.title;

      const desc = document.createElement("div");
      desc.classList.add("doclib-tl-desc");
      desc.innerText = event.description;

      const dot = document.createElement("div");
      dot.classList.add("doclib-tl-dot");
      dot.style.background = event.color;

      content.appendChild(date);
      content.appendChild(title);
      content.appendChild(desc);

      el.appendChild(content);
      el.appendChild(dot);
      this.wrapper.appendChild(el);
    });

    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-tl-edit");

      const header = document.createElement("div");
      header.style.cssText = "display:grid;grid-template-columns:1fr 2fr 3fr 40px 30px;gap:8px;font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;";
      header.innerHTML = "<span>Date</span><span>Title</span><span>Description</span><span>Color</span><span></span>";
      editArea.appendChild(header);

      this.data.events.forEach((event, idx) => {
        const row = document.createElement("div");
        row.classList.add("doclib-tl-edit-row");

        const mkInput = (val: string, update: (v: string) => void) => {
          const inp = document.createElement("input");
          inp.classList.add("doclib-tl-input");
          inp.value = val;
          inp.addEventListener("input", () => { update(inp.value); this.buildUI(); });
          return inp;
        };

        row.appendChild(mkInput(event.date, (v) => event.date = v));
        row.appendChild(mkInput(event.title, (v) => event.title = v));
        row.appendChild(mkInput(event.description, (v) => event.description = v));

        const colorInp = document.createElement("input");
        colorInp.type = "color";
        colorInp.value = event.color;
        colorInp.style.width = "100%";
        colorInp.style.border = "none";
        colorInp.style.padding = "0";
        colorInp.style.background = "transparent";
        colorInp.style.cursor = "pointer";
        colorInp.addEventListener("input", () => { event.color = colorInp.value; this.buildUI(); });
        row.appendChild(colorInp);

        const del = document.createElement("button");
        del.classList.add("doclib-tl-del");
        del.innerText = "x";
        del.addEventListener("click", () => { this.data.events.splice(idx, 1); this.buildUI(); });
        row.appendChild(del);

        editArea.appendChild(row);
      });

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-tl-add-btn");
      addBtn.innerText = "Add Event";
      addBtn.addEventListener("click", () => {
        this.data.events.push({ id: this.mkId(), date: "New Date", title: "New Event", description: "Event description", color: "#64748b" });
        this.buildUI();
      });

      editArea.appendChild(addBtn);
      this.wrapper.appendChild(editArea);
    }
  }

  save() {
    return this.data;
  }
}
