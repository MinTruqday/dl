import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTimeline implements BlockTool {
  static readonly feature = {
    id: "DocLibTimeline",
    title: "DocLib Timeline",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4187bedb46182280"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="18,20 7,19 6,11 4,13 11,4 15,10"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { items: { title: string; date: string; desc: string }[] };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Timeline",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4187bedb46182280"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="18,20 7,19 6,11 4,13 11,4 15,10"/></svg>',
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
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      items:
        data.items && data.items.length > 0
          ? data.items
          : [
              {
                title: "DocLib Start Project",
                date: "Jan 2024",
                desc: "Kickoff and detailed planning.",
              },
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
            .doclib-tl-wrapper { position: relative; margin: 24px 0; padding-left: 24px; }
            .doclib-tl-wrapper::before { content: ''; position: absolute; left: 8px; top: 8px; bottom: 8px; width: 2px; background: hsl(var(--border)); }
            .doclib-tl-item { position: relative; margin-bottom: 24px; }
            .doclib-tl-item:last-child { margin-bottom: 0; }
            .doclib-tl-dot { position: absolute; left: -21px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: hsl(var(--brand)); border: 3px solid hsl(var(--surface)); box-shadow: 0 0 0 2px hsl(var(--brand)); }
            .doclib-tl-content { background: hsl(var(--surface-raised)); border: 1px solid hsl(var(--border)); border-radius: 8px; padding: 16px; position: relative; }
            .doclib-tl-content::before { content: ''; position: absolute; left: -6px; top: 6px; width: 10px; height: 10px; background: hsl(var(--surface-raised)); border-left: 1px solid hsl(var(--border)); border-bottom: 1px solid hsl(var(--border)); transform: rotate(45deg); }
            .doclib-tl-title { font-weight: 700; font-size: 1.1em; color: hsl(var(--ink)); outline: none; margin-bottom: 4px; }
            .doclib-tl-title:empty::before { content: 'Enter event name'; color: hsl(var(--ink-faint)); }
            .doclib-tl-date { font-size: 0.85em; color: hsl(var(--brand)); font-weight: 600; outline: none; margin-bottom: 8px; }
            .doclib-tl-date:empty::before { content: 'Time'; color: #93c5fd; }
            .doclib-tl-desc { font-size: 0.95em; color: hsl(var(--ink-muted)); outline: none; line-height: 1.5; }
            .doclib-tl-desc:empty::before { content: 'Detailed description'; color: hsl(var(--ink-faint)); }
            .doclib-tl-btn { margin-top: 16px; padding: 8px 16px; background: hsl(var(--surface-quiet)); border: 1px dashed hsl(var(--border)); border-radius: 8px; color: hsl(var(--ink-muted)); font-weight: 500; cursor: pointer; width: 100%; text-align: center; transition: background 0.2s; }
            .doclib-tl-btn:hover { background: hsl(var(--border)); }
            .doclib-tl-rm { position: absolute; top: 8px; right: 8px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: #fee2e2; color: hsl(var(--danger)); border-radius: 4px; cursor: pointer; border: none; opacity: 0; transition: opacity 0.2s; }
            .doclib-tl-content:hover .doclib-tl-rm { opacity: 1; }
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
    container.classList.add("doclib-tl-wrapper");

    this.data.items.forEach((item, index) => {
      const el = document.createElement("div");
      el.classList.add("doclib-tl-item");

      const dot = document.createElement("div");
      dot.classList.add("doclib-tl-dot");

      const content = document.createElement("div");
      content.classList.add("doclib-tl-content");

      const title = document.createElement("div");
      title.classList.add("doclib-tl-title");
      title.contentEditable = !this.readOnly ? "true" : "false";
      title.innerHTML = item.title;
      title.addEventListener("input", () => (item.title = title.innerHTML));

      const date = document.createElement("div");
      date.classList.add("doclib-tl-date");
      date.contentEditable = !this.readOnly ? "true" : "false";
      date.innerHTML = item.date;
      date.addEventListener("input", () => (item.date = date.innerHTML));

      const desc = document.createElement("div");
      desc.classList.add("doclib-tl-desc");
      desc.contentEditable = !this.readOnly ? "true" : "false";
      desc.innerHTML = item.desc;
      desc.addEventListener("input", () => (item.desc = desc.innerHTML));

      content.appendChild(title);
      content.appendChild(date);
      content.appendChild(desc);

      if (!this.readOnly && this.data.items.length > 1) {
        const rmBtn = document.createElement("button");
        rmBtn.classList.add("doclib-tl-rm");
        rmBtn.innerHTML = "&times;";
        rmBtn.addEventListener("click", () => {
          this.data.items.splice(index, 1);
          this.buildUI();
        });
        content.appendChild(rmBtn);
      }

      el.appendChild(dot);
      el.appendChild(content);
      container.appendChild(el);
    });

    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-tl-btn");
      addBtn.innerText = "+ Add Timeline Milestone";
      addBtn.addEventListener("click", () => {
        this.data.items.push({ title: "", date: "", desc: "" });
        this.buildUI();
      });
      this.wrapper.appendChild(addBtn);
    }
  }

  save() {
    return this.data;
  }
}
