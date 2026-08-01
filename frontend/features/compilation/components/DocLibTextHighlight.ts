import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibTextHighlight implements InlineTool {
  static readonly feature = {
    id: "DocLibTextHighlight",
    title: "Tô sáng",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a21b4ad9c88e1fea"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,14 10,17 17,10 18,17 9,20 5,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLElement | null = null;
  private state: boolean = false;
  private colorPicker: HTMLElement | null = null;

  static get isInline() {
    return true;
  }
  static get sanitize() {
    return { mark: { "data-color": true, style: true } };
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a21b4ad9c88e1fea"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,14 10,17 17,10 18,17 9,20 5,19"/></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);

    if (!document.getElementById("doclib-text-highlight-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-text-highlight-styles";
      style.innerHTML = `
            mark[data-color] { padding: 2px 4px; border-radius: 4px; color: inherit; }
            .doclib-th-picker { position: absolute; top: 100%; left: 0; background: hsl(var(--surface)); border: 1px solid hsl(var(--border)); border-radius: 6px; padding: 4px; display: flex; gap: 4px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); z-index: 100; margin-top: 4px; }
            .doclib-th-color { width: 20px; height: 20px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(0,0,0,0.1); }
            .doclib-th-color:hover { transform: scale(1.1); }
            .doclib-th-clear { display: flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; cursor: pointer; border: 1px solid hsl(var(--border)); background: hsl(var(--surface-raised)); font-size: 12px; }
        `;
      document.head.appendChild(style);
    }

    return this.button;
  }

  renderActions() {
    this.colorPicker = document.createElement("div");
    this.colorPicker.classList.add("doclib-th-picker");
    this.colorPicker.style.display = "none";

    const colors = [
      { name: "yellow", value: "hsl(var(--warning-soft))" },
      { name: "green", value: "hsl(var(--brand-soft))" },
      { name: "blue", value: "hsl(var(--brand-soft))" },
      { name: "pink", value: "#fbcfe8" },
      { name: "purple", value: "#e9d5ff" },
    ];

    colors.forEach((c) => {
      const btn = document.createElement("div");
      btn.classList.add("doclib-th-color");
      btn.style.backgroundColor = c.value;
      btn.addEventListener("click", () => {
        this.applyColor(c.value);
        this.hidePicker();
      });
      this.colorPicker!.appendChild(btn);
    });

    const clearBtn = document.createElement("div");
    clearBtn.classList.add("doclib-th-clear");
    clearBtn.innerHTML = "&times;";
    clearBtn.addEventListener("click", () => {
      this.removeColor();
      this.hidePicker();
    });
    this.colorPicker.appendChild(clearBtn);

    return this.colorPicker;
  }

  surround(range: Range) {
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag("MARK", "data-color");

    if (termWrapper) {
      this.togglePicker();
    } else {
      this.wrap(range, "hsl(var(--warning-soft))");
    }
  }

  private togglePicker() {
    if (!this.colorPicker) return;
    if (this.colorPicker.style.display === "none") {
      this.colorPicker.style.display = "flex";
    } else {
      this.colorPicker.style.display = "none";
    }
  }

  private hidePicker() {
    if (this.colorPicker) this.colorPicker.style.display = "none";
  }

  wrap(range: Range, color: string) {
    const mark = document.createElement("mark");
    mark.dataset.color = "true";
    mark.style.backgroundColor = color;
    mark.appendChild(range.extractContents());
    range.insertNode(mark);
    this.api.selection.expandToTag(mark);
  }

  applyColor(color: string) {
    const termWrapper = this.api.selection.findParentTag("MARK", "data-color");
    if (termWrapper) {
      termWrapper.style.backgroundColor = color;
    }
  }

  removeColor() {
    const termWrapper = this.api.selection.findParentTag("MARK", "data-color");
    if (termWrapper) {
      this.unwrap(termWrapper);
    }
  }

  unwrap(termWrapper: HTMLElement) {
    this.api.selection.expandToTag(termWrapper);
    const sel = window.getSelection();
    const range = sel?.getRangeAt(0);
    const unwrappedContent = range?.extractContents();
    if (unwrappedContent) {
      termWrapper.parentNode?.replaceChild(unwrappedContent, termWrapper);
    }
  }

  checkState() {
    const termTag = this.api.selection.findParentTag("MARK", "data-color");
    this.state = !!termTag;
    if (this.state) {
      this.button?.classList.add(this.api.styles.inlineToolButtonActive);
    } else {
      this.button?.classList.remove(this.api.styles.inlineToolButtonActive);
      this.hidePicker();
    }
    return this.state;
  }
}
