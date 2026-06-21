import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibNumberCounter implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { stats: { value: string; label: string; prefix: string; suffix: string; color: string }[] };
  private readOnly: boolean;
  private observer: IntersectionObserver | null = null;

  static get toolbox() {
    return {
      title: "DocLib Number Counter",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      stats: data?.stats && data.stats.length > 0 ? data.stats : [
        { value: "10000", label: "Users", prefix: "", suffix: "+", color: "#0284c7" },
        { value: "500", label: "Documents", prefix: "", suffix: "K", color: "#059669" },
        { value: "99", label: "Satisfaction", prefix: "", suffix: "%", color: "#7c3aed" },
        { value: "24", label: "Support", prefix: "", suffix: "/7", color: "#d97706" },
      ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-counter-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-counter-styles";
      style.innerHTML = `
        .doclib-counter-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px 24px; background: #fff; margin: 12px 0; }
        .doclib-counter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 20px; }
        .doclib-counter-item { text-align: center; }
        .doclib-counter-number { font-size: 36px; font-weight: 800; line-height: 1; }
        .doclib-counter-label { font-size: 13px; color: #64748b; margin-top: 6px; font-weight: 500; }
        .doclib-counter-edit { border-top: 1px solid #f1f5f9; margin-top: 20px; padding-top: 16px; }
        .doclib-counter-row { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 28px; gap: 6px; align-items: center; margin-bottom: 6px; }
        .doclib-counter-input { padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; width: 100%; box-sizing: border-box; }
        .doclib-counter-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
        .doclib-counter-add { margin-top: 6px; padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 11px; cursor: pointer; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private animateNumber(el: HTMLElement, target: number, duration: number) {
    const start = Date.now();
    const step = () => {
      const elapsed = Date.now() - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.innerText = Math.round(eased * target).toLocaleString("vi-VN");
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  private buildUI() {
    if (this.observer) { this.observer.disconnect(); this.observer = null; }
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-counter-wrapper");

    const grid = document.createElement("div");
    grid.classList.add("doclib-counter-grid");

    const numberEls: HTMLElement[] = [];

    this.data.stats.forEach((stat) => {
      const item = document.createElement("div");
      item.classList.add("doclib-counter-item");

      const numRow = document.createElement("div");
      numRow.style.display = "flex";
      numRow.style.justifyContent = "center";
      numRow.style.alignItems = "baseline";
      numRow.style.gap = "2px";

      if (stat.prefix) {
        const pre = document.createElement("span");
        pre.style.cssText = `font-size:18px;font-weight:700;color:${stat.color};`;
        pre.innerText = stat.prefix;
        numRow.appendChild(pre);
      }

      const numEl = document.createElement("span");
      numEl.classList.add("doclib-counter-number");
      numEl.style.color = stat.color;
      numEl.innerText = "0";
      numberEls.push(numEl);
      numRow.appendChild(numEl);

      if (stat.suffix) {
        const suf = document.createElement("span");
        suf.style.cssText = `font-size:18px;font-weight:700;color:${stat.color};`;
        suf.innerText = stat.suffix;
        numRow.appendChild(suf);
      }

      const label = document.createElement("div");
      label.classList.add("doclib-counter-label");
      label.innerText = stat.label;

      item.appendChild(numRow);
      item.appendChild(label);
      grid.appendChild(item);
    });

    this.wrapper.appendChild(grid);

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          this.data.stats.forEach((stat, i) => {
            const target = parseFloat(stat.value.replace(/[^0-9.]/g, "")) || 0;
            this.animateNumber(numberEls[i], target, 1200);
          });
          this.observer?.disconnect();
        }
      });
    }, { threshold: 0.3 });

    this.observer.observe(this.wrapper);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-counter-edit");

      const header = document.createElement("div");
      header.style.cssText = "display:grid;grid-template-columns:2fr 1fr 1fr 1fr 28px;gap:6px;font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;";
      header.innerHTML = "<span>Label</span><span>Value</span><span>Prefix</span><span>Suffix</span><span></span>";
      edit.appendChild(header);

      const rows = document.createElement("div");

      const renderRows = () => {
        rows.innerHTML = "";
        this.data.stats.forEach((stat, i) => {
          const row = document.createElement("div");
          row.classList.add("doclib-counter-row");

          const mkInput = (value: string, onChange: (v: string) => void) => {
            const inp = document.createElement("input");
            inp.classList.add("doclib-counter-input");
            inp.value = value;
            inp.addEventListener("input", () => { onChange(inp.value); this.buildUI(); });
            return inp;
          };

          row.appendChild(mkInput(stat.label, (v) => { stat.label = v; }));
          row.appendChild(mkInput(stat.value, (v) => { stat.value = v; }));
          row.appendChild(mkInput(stat.prefix, (v) => { stat.prefix = v; }));
          row.appendChild(mkInput(stat.suffix, (v) => { stat.suffix = v; }));

          const del = document.createElement("button");
          del.classList.add("doclib-counter-del");
          del.innerText = "x";
          del.addEventListener("click", () => { this.data.stats.splice(i, 1); this.buildUI(); });
          row.appendChild(del);
          rows.appendChild(row);
        });
      };

      renderRows();
      edit.appendChild(rows);

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-counter-add");
      addBtn.innerText = "Add metric";
      const colors = ["#0284c7", "#059669", "#7c3aed", "#d97706", "#dc2626"];
      addBtn.addEventListener("click", () => {
        this.data.stats.push({ value: "100", label: "New metric", prefix: "", suffix: "+", color: colors[this.data.stats.length % colors.length] });
        this.buildUI();
      });
      edit.appendChild(addBtn);
      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
