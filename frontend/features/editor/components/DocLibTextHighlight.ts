import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibTextHighlight implements InlineTool {
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
    this.button.type = "button";
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path></svg>';
    this.button.classList.add(this.api.styles.inlineToolButton);

    if (!document.getElementById("doclib-text-highlight-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-text-highlight-styles";
      style.innerHTML = `
            mark[data-color] { padding: 2px 4px; border-radius: 4px; color: inherit; }
            .doclib-th-picker { position: absolute; top: 100%; left: 0; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; display: flex; gap: 4px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); z-index: 100; margin-top: 4px; }
            .doclib-th-color { width: 20px; height: 20px; border-radius: 4px; cursor: pointer; border: 1px solid rgba(0,0,0,0.1); }
            .doclib-th-color:hover { transform: scale(1.1); }
            .doclib-th-clear { display: flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; cursor: pointer; border: 1px solid #e2e8f0; background: #f8fafc; font-size: 12px; }
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
      { name: "yellow", value: "#fef08a" },
      { name: "green", value: "#bbf7d0" },
      { name: "blue", value: "#bfdbfe" },
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
      this.wrap(range, "#fef08a");
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
