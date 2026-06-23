import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibReviewSummary implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Review Summary",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      average: data?.average || "4.8",
      total: data?.total || "1,234",
      s5: data?.s5 || 80,
      s4: data?.s4 || 10,
      s3: data?.s3 || 5,
      s2: data?.s2 || 3,
      s1: data?.s1 || 2,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-rs { display: flex; gap: 24px; padding: 24px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; font-family: sans-serif; max-width: 500px; margin: 16px auto; }
      .doclib-rs-left { display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .doclib-rs-avg { font-size: 48px; font-weight: 800; color: #0f172a; outline: none; line-height: 1; }
      .doclib-rs-stars { color: #f59e0b; font-size: 20px; margin: 8px 0; }
      .doclib-rs-total { font-size: 13px; color: #64748b; outline: none; }
      .doclib-rs-right { flex: 1; display: flex; flex-direction: column; gap: 8px; justify-content: center; }
      .doclib-rs-row { display: flex; align-items: center; gap: 8px; }
      .doclib-rs-label { font-size: 13px; color: #475569; width: 45px; display: flex; align-items: center; gap: 4px; }
      .doclib-rs-star-icon { color: #f59e0b; font-size: 12px; }
      .doclib-rs-bar-bg { flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; position: relative; }
      .doclib-rs-bar-fill { height: 100%; background: #f59e0b; border-radius: 4px; transition: width 0.3s; }
      .doclib-rs-pct { font-size: 12px; color: #64748b; width: 30px; text-align: right; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-rs");

    const left = document.createElement("div");
    left.classList.add("doclib-rs-left");

    const avgEl = document.createElement("div");
    avgEl.classList.add("doclib-rs-avg");
    avgEl.innerText = this.data.average;
    if (!this.readOnly) {
      avgEl.contentEditable = "true";
      avgEl.addEventListener("input", () => { this.data.average = avgEl.innerText; });
    }

    const starsEl = document.createElement("div");
    starsEl.classList.add("doclib-rs-stars");
    starsEl.innerHTML = "★★★★★";

    const totalEl = document.createElement("div");
    totalEl.classList.add("doclib-rs-total");
    totalEl.innerText = this.data.total;
    if (!this.readOnly) {
      totalEl.contentEditable = "true";
      totalEl.addEventListener("input", () => { this.data.total = totalEl.innerText; });
    }

    left.appendChild(avgEl);
    left.appendChild(starsEl);
    left.appendChild(totalEl);
    container.appendChild(left);

    const right = document.createElement("div");
    right.classList.add("doclib-rs-right");

    const buildRow = (stars: number, key: string) => {
      const row = document.createElement("div");
      row.classList.add("doclib-rs-row");

      const lbl = document.createElement("div");
      lbl.classList.add("doclib-rs-label");
      lbl.innerHTML = `${stars} <span class="doclib-rs-star-icon">★</span>`;

      const barBg = document.createElement("div");
      barBg.classList.add("doclib-rs-bar-bg");

      const barFill = document.createElement("div");
      barFill.classList.add("doclib-rs-bar-fill");
      barFill.style.width = `${this.data[key]}%`;
      barBg.appendChild(barFill);

      const pct = document.createElement("div");
      pct.classList.add("doclib-rs-pct");
      pct.innerText = `${this.data[key]}%`;

      if (!this.readOnly) {
        pct.contentEditable = "true";
        pct.addEventListener("input", () => {
          const val = parseInt(pct.innerText.replace("%", "")) || 0;
          this.data[key] = val;
          barFill.style.width = `${val}%`;
        });
      }

      row.appendChild(lbl);
      row.appendChild(barBg);
      row.appendChild(pct);
      return row;
    };

    right.appendChild(buildRow(5, "s5"));
    right.appendChild(buildRow(4, "s4"));
    right.appendChild(buildRow(3, "s3"));
    right.appendChild(buildRow(2, "s2"));
    right.appendChild(buildRow(1, "s1"));

    container.appendChild(right);
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
