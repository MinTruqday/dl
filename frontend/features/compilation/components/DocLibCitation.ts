import { API, BlockTool } from "@editorjs/editorjs";

type CitationStyle = "APA" | "MLA" | "Chicago";
type CitationData = {
  style: CitationStyle;
  author: string;
  year: string;
  title: string;
  source: string;
  url: string;
};
type CitationTextKey = Exclude<keyof CitationData, "style">;

export default class DocLibCitation implements BlockTool {
  static readonly feature = {
    id: "DocLibCitation",
    title: "DocLib Citation",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d8730ef74236f09c"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,17 18,13 19,7 6,7 18,12 5,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: CitationData;
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Citation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d8730ef74236f09c"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,17 18,13 19,7 6,7 18,12 5,4"/></svg>',
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
      style: data?.style || "APA",
      author: data?.author || "",
      year: data?.year || "",
      title: data?.title || "",
      source: data?.source || "",
      url: data?.url || "",
    };
  }

  private formatCitation(d: typeof this.data): string {
    const { style, author, year, title, source, url } = d;
    if (style === "APA") {
      let c = "";
      if (author) c += `${author}`;
      if (year) c += ` (${year}).`;
      if (title) c += ` <em>${title}</em>.`;
      if (source) c += ` ${source}.`;
      if (url)
        c += ` Retrieved from <a href="${url}" target="_blank" style="color:hsl(var(--brand))">${url}</a>`;
      return c;
    }
    if (style === "MLA") {
      let c = "";
      if (author) c += `${author}.`;
      if (title) c += ` "<em>${title}</em>."`;
      if (source) c += ` ${source},`;
      if (year) c += ` ${year}.`;
      if (url)
        c += ` <a href="${url}" target="_blank" style="color:hsl(var(--brand))">${url}</a>`;
      return c;
    }
    let c = "";
    if (author) c += `${author}.`;
    if (title) c += ` "<em>${title}</em>."`;
    if (source) c += ` <em>${source}</em>`;
    if (year) c += ` (${year}).`;
    if (url)
      c += ` <a href="${url}" target="_blank" style="color:hsl(var(--brand))">${url}</a>`;
    return c;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-citation-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-citation-styles";
      style.innerHTML = `
        .doclib-citation-wrapper { border: 1px solid hsl(var(--border)); border-radius: 8px; padding: 20px; background: hsl(var(--surface)); margin: 12px 0; }
        .doclib-citation-style-row { display: flex; gap: 8px; margin-bottom: 16px; }
        .doclib-citation-style-btn { padding: 6px 14px; border: 1px solid hsl(var(--border)); border-radius: 4px; background: hsl(var(--surface)); font-size: 13px; font-weight: 500; color: hsl(var(--ink-muted)); cursor: pointer; }
        .doclib-citation-style-btn.active { background: hsl(var(--ink)); color: hsl(var(--surface)); border-color: hsl(var(--ink)); }
        .doclib-citation-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
        .doclib-citation-field { display: flex; flex-direction: column; gap: 4px; }
        .doclib-citation-field label { font-size: 11px; font-weight: 600; color: hsl(var(--ink-faint)); text-transform: uppercase; }
        .doclib-citation-field input { padding: 8px 10px; border: 1px solid hsl(var(--border)); border-radius: 6px; font-size: 13px; outline: none; }
        .doclib-citation-output { border-top: 1px solid hsl(var(--border)); padding-top: 14px; font-size: 14px; line-height: 1.7; color: hsl(var(--ink)); background: hsl(var(--surface-raised)); padding: 14px; border-radius: 6px; }
        .doclib-citation-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
        .doclib-citation-copy { padding: 6px 12px; background: hsl(var(--surface-quiet)); border: 1px solid hsl(var(--border)); border-radius: 4px; font-size: 12px; cursor: pointer; }
        .doclib-citation-readonly { border-left: 3px solid hsl(var(--brand)); padding: 12px 16px; background: hsl(var(--brand-soft)); border-radius: 0 6px 6px 0; font-size: 14px; line-height: 1.7; color: hsl(var(--ink)); }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-citation-wrapper");

    if (this.readOnly) {
      const output = document.createElement("div");
      output.classList.add("doclib-citation-readonly");
      output.innerHTML =
        this.formatCitation(this.data) || "<em>No citation data</em>";
      this.wrapper.appendChild(output);
      return;
    }

    const styleRow = document.createElement("div");
    styleRow.classList.add("doclib-citation-style-row");

    const styles: CitationStyle[] = ["APA", "MLA", "Chicago"];
    styles.forEach((s) => {
      const btn = document.createElement("button");
      btn.classList.add("doclib-citation-style-btn");
      if (this.data.style === s) btn.classList.add("active");
      btn.innerText = s;
      btn.addEventListener("click", () => {
        this.data.style = s;
        styleRow
          .querySelectorAll(".doclib-citation-style-btn")
          .forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        output.innerHTML = this.formatCitation(this.data);
      });
      styleRow.appendChild(btn);
    });

    const fields: {
      key: CitationTextKey;
      label: string;
      placeholder: string;
    }[] = [
      { key: "author", label: "Author", placeholder: "Jane Doe" },
      { key: "year", label: "Year", placeholder: "2024" },
      { key: "title", label: "Title", placeholder: "Article or book title" },
      { key: "source", label: "Source Journal", placeholder: "Journal of" },
      { key: "url", label: "URL", placeholder: "https://" },
    ];

    const fieldsGrid = document.createElement("div");
    fieldsGrid.classList.add("doclib-citation-fields");

    const output = document.createElement("div");
    output.classList.add("doclib-citation-output");
    output.innerHTML = this.formatCitation(this.data);

    fields.forEach(({ key, label, placeholder }) => {
      const field = document.createElement("div");
      field.classList.add("doclib-citation-field");
      if (key === "url") field.style.gridColumn = "1 / -1";

      const lbl = document.createElement("label");
      lbl.innerText = label;

      const input = document.createElement("input");
      input.value = this.data[key] as string;
      input.placeholder = placeholder;
      input.addEventListener("input", () => {
        this.data[key] = input.value;
        output.innerHTML = this.formatCitation(this.data);
      });

      field.appendChild(lbl);
      field.appendChild(input);
      fieldsGrid.appendChild(field);
    });

    const actions = document.createElement("div");
    actions.classList.add("doclib-citation-actions");
    const copyBtn = document.createElement("button");
    copyBtn.classList.add("doclib-citation-copy");
    copyBtn.innerText = "Copy";
    copyBtn.addEventListener("click", () => {
      const text = output.innerText;
      navigator.clipboard.writeText(text).then(() => {
        copyBtn.innerText = "Copied";
        setTimeout(() => {
          copyBtn.innerText = "Copy";
        }, 1500);
      });
    });
    actions.appendChild(copyBtn);

    this.wrapper.appendChild(styleRow);
    this.wrapper.appendChild(fieldsGrid);
    this.wrapper.appendChild(output);
    this.wrapper.appendChild(actions);
  }

  save() {
    return this.data;
  }
}
