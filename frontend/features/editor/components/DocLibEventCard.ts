import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibEventCard implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    title: string;
    description: string;
    date: string;
    time: string;
    location: string;
    url: string;
    color: string;
  };
  private readOnly: boolean;
  private timerInterval: ReturnType<typeof setInterval> | null = null;

  static get toolbox() {
    return {
      title: "DocLib Event Card",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 7);
    this.data = {
      title: data?.title || "",
      description: data?.description || "",
      date: data?.date || tomorrow.toISOString().split("T")[0],
      time: data?.time || "",
      location: data?.location || "",
      url: data?.url || "",
      color: data?.color || "#ffffff",
    };
  }

  private getCountdown(dateStr: string, timeStr: string): string {
    const target = new Date(`${dateStr}T${timeStr}:00`);
    const now = new Date();
    const diff = target.getTime() - now.getTime();
    if (diff <= 0) return "Event has ended";
    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    if (days > 0) return `In ${days} days ${hours} hours`;
    if (hours > 0) return `In ${hours} hours ${mins} minutes`;
    return `In ${mins} minutes`;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-event-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-event-styles";
      style.innerHTML = `
        .doclib-event-wrapper { border-radius: 12px; overflow: hidden; margin: 12px 0; }
        .doclib-event-header { padding: 20px 24px; color: #fff; }
        .doclib-event-badge { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85; margin-bottom: 6px; }
        .doclib-event-title { font-size: 22px; font-weight: 700; }
        .doclib-event-body { background: #fff; border: 1px solid #e2e8f0; border-top: none; padding: 20px 24px; }
        .doclib-event-desc { font-size: 14px; color: #64748b; margin-bottom: 16px; line-height: 1.5; }
        .doclib-event-meta { display: flex; flex-direction: column; gap: 8px; }
        .doclib-event-meta-row { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #475569; }
        .doclib-event-meta-icon { font-size: 16px; }
        .doclib-event-countdown { margin-top: 16px; padding: 12px 16px; border-radius: 8px; display: flex; align-items: center; gap: 10px; }
        .doclib-event-countdown-text { font-size: 14px; font-weight: 600; }
        .doclib-event-actions { display: flex; gap: 10px; margin-top: 16px; }
        .doclib-event-btn { padding: 9px 18px; border-radius: 7px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; text-decoration: none; display: inline-block; }
        .doclib-event-edit { background: #f8fafc; border: 1px solid #e2e8f0; border-top: none; padding: 16px 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .doclib-event-field { display: flex; flex-direction: column; gap: 3px; }
        .doclib-event-field label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-event-field input { padding: 7px 9px; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 12px; outline: none; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (this.timerInterval) { clearInterval(this.timerInterval); this.timerInterval = null; }
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-event-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-event-header");
    header.style.background = this.data.color;

    const badge = document.createElement("div");
    badge.classList.add("doclib-event-badge");
    badge.innerText = " EVENT";

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-event-title");
    titleEl.innerText = this.data.title;

    header.appendChild(badge);
    header.appendChild(titleEl);

    const body = document.createElement("div");
    body.classList.add("doclib-event-body");

    const desc = document.createElement("div");
    desc.classList.add("doclib-event-desc");
    desc.innerText = this.data.description;

    const metaList = document.createElement("div");
    metaList.classList.add("doclib-event-meta");

    const date = new Date(`${this.data.date}T${this.data.time}:00`);
    const dateStr = date.toLocaleDateString("vi-VN", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

    [
      { icon: "", text: `${dateStr} at ${this.data.time}` },
      { icon: "", text: this.data.location },
    ].forEach(({ icon, text }) => {
      if (!text) return;
      const row = document.createElement("div");
      row.classList.add("doclib-event-meta-row");
      row.innerHTML = `<span class="doclib-event-meta-icon">${icon}</span><span>${text}</span>`;
      metaList.appendChild(row);
    });

    const countdown = document.createElement("div");
    countdown.classList.add("doclib-event-countdown");
    countdown.style.background = this.data.color + "15";

    const countdownText = document.createElement("div");
    countdownText.classList.add("doclib-event-countdown-text");
    countdownText.style.color = this.data.color;
    countdownText.innerText = this.getCountdown(this.data.date, this.data.time);
    countdown.appendChild(countdownText);

    this.timerInterval = setInterval(() => {
      countdownText.innerText = this.getCountdown(this.data.date, this.data.time);
    }, 60000);

    const actions = document.createElement("div");
    actions.classList.add("doclib-event-actions");

    if (this.data.url) {
      const rsvpBtn = document.createElement("a");
      rsvpBtn.classList.add("doclib-event-btn");
      rsvpBtn.style.background = this.data.color;
      rsvpBtn.style.color = "#fff";
      rsvpBtn.href = this.data.url;
      rsvpBtn.target = "_blank";
      rsvpBtn.innerText = "Register";
      actions.appendChild(rsvpBtn);
    }

    const calBtn = document.createElement("button");
    calBtn.classList.add("doclib-event-btn");
    calBtn.style.background = "#f1f5f9";
    calBtn.style.color = "#475569";
    calBtn.innerText = " Add to Calendar";
    calBtn.addEventListener("click", () => {
      const start = `${this.data.date}T${this.data.time}:00`;
      const ics = `BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:${this.data.title}\nDTSTART:${start.replace(/-|:/g, "")}\nLOCATION:${this.data.location}\nDESCRIPTION:${this.data.description}\nEND:VEVENT\nEND:VCALENDAR`;
      const blob = new Blob([ics], { type: "text/calendar" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "event.ics";
      a.click();
      URL.revokeObjectURL(url);
    });
    actions.appendChild(calBtn);

    body.appendChild(desc);
    body.appendChild(metaList);
    body.appendChild(countdown);
    body.appendChild(actions);

    this.wrapper.appendChild(header);
    this.wrapper.appendChild(body);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-event-edit");

      const fields: { key: keyof typeof this.data; label: string; type?: string }[] = [
        { key: "title", label: "Title" },
        { key: "location", label: "Location" },
        { key: "date", label: "Date", type: "date" },
        { key: "time", label: "Time", type: "time" },
        { key: "url", label: "Registration URL" },
        { key: "color", label: "Color", type: "color" },
        { key: "description", label: "Description" },
      ];

      fields.forEach(({ key, label, type }) => {
        const field = document.createElement("div");
        field.classList.add("doclib-event-field");
        if (key === "description" || key === "url") field.style.gridColumn = "1 / -1";
        const lbl = document.createElement("label");
        lbl.innerText = label;
        const input = document.createElement("input");
        input.type = type || "text";
        input.value = this.data[key] as string;
        let timeout: ReturnType<typeof setTimeout>;
        input.addEventListener("input", () => {
          (this.data as any)[key] = input.value;
          clearTimeout(timeout);
          timeout = setTimeout(() => this.buildUI(), 400);
        });
        field.appendChild(lbl);
        field.appendChild(input);
        edit.appendChild(field);
      });

      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
