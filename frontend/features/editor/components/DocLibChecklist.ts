import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibChecklist implements BlockTool {
  private api: API;
  private data: { items: { text: string; checked: boolean }[] };
  private wrapper: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib Checklist",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      items: Array.isArray(data?.items)
        ? data.items
        : [{ text: "", checked: false }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-checklist-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-checklist-styles";
      style.innerHTML = `
            .doclib-checklist-item { display: flex; align-items: flex-start; margin-bottom: 8px; }
            .doclib-checklist-checkbox { width: 20px; height: 20px; border: 1px solid #ccc; border-radius: 4px; margin-right: 10px; cursor: pointer; display: flex; justify-content: center; align-items: center; flex-shrink: 0; margin-top: 2px; }
            .doclib-checklist-checkbox.checked { background-color: #388ae5; border-color: #388ae5; }
            .doclib-checklist-checkbox.checked::after { content: ''; width: 5px; height: 10px; border: solid white; border-width: 0 2px 2px 0; transform: rotate(45deg); margin-bottom: 2px; }
            .doclib-checklist-text { flex-grow: 1; outline: none; min-height: 24px; line-height: 1.5; padding: 2px 0; }
            .doclib-checklist-item.checked .doclib-checklist-text { text-decoration: line-through; color: #999; }
            .doclib-checklist-text:empty::before { content: 'Enter text'; color: #aaa; pointer-events: none; }
        `;
      document.head.appendChild(style);
    }

    this.data.items.forEach((item) => {
      this.wrapper!.appendChild(this.createRow(item.text, item.checked));
    });

    return this.wrapper;
  }

  private createRow(text: string, checked: boolean) {
    const row = document.createElement("div");
    row.classList.add("doclib-checklist-item");
    if (checked) row.classList.add("checked");

    const checkbox = document.createElement("div");
    checkbox.classList.add("doclib-checklist-checkbox");
    if (checked) checkbox.classList.add("checked");

    const input = document.createElement("div");
    input.classList.add("doclib-checklist-text");
    input.contentEditable = "true";
    input.innerHTML = text;

    checkbox.addEventListener("click", () => {
      checked = !checked;
      checkbox.classList.toggle("checked", checked);
      row.classList.toggle("checked", checked);
      this.api.saver.save();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const newRow = this.createRow("", false);
        row.after(newRow);
        (newRow.querySelector(".doclib-checklist-text") as HTMLElement).focus();
      } else if (e.key === "Backspace" && input.innerHTML === "") {
        e.preventDefault();
        if (this.wrapper!.children.length > 1) {
          const prev = row.previousElementSibling;
          row.remove();
          if (prev) {
            const prevInput = prev.querySelector(
              ".doclib-checklist-text",
            ) as HTMLElement;
            prevInput.focus();
            const range = document.createRange();
            const sel = window.getSelection();
            range.selectNodeContents(prevInput);
            range.collapse(false);
            sel?.removeAllRanges();
            sel?.addRange(range);
          }
        }
      }
    });

    row.appendChild(checkbox);
    row.appendChild(input);
    return row;
  }

  save() {
    const items: { text: string; checked: boolean }[] = [];
    if (this.wrapper) {
      Array.from(this.wrapper.children).forEach((row) => {
        const checked = row.classList.contains("checked");
        const text = (
          row.querySelector(".doclib-checklist-text") as HTMLElement
        ).innerHTML;
        items.push({ text, checked });
      });
    }
    return { items };
  }

  static get sanitize() {
    return {
      items: {
        text: true,
        checked: true,
      },
    };
  }
}
