import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibHyperlink implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tooltipInput: HTMLInputElement | null = null;
  private spanTooltip: HTMLElement | null = null;

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Hyperlink";
  }

  get state() {
    return this._state;
  }
  set state(s: boolean) {
    this._state = s;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, s);
    }
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>';

    return this.button;
  }

  surround(range: Range) {
    if (this.state) {
      this.unwrap(range);
    } else {
      this.wrap(range);
    }
  }

  wrap(range: Range) {
    const selectedText = range.extractContents();
    this.spanTooltip = document.createElement("a");
    this.spanTooltip.classList.add("doclib-hyperlink");
    this.spanTooltip.setAttribute("target", "_blank");
    this.spanTooltip.setAttribute("rel", "nofollow noopener noreferrer");
    this.spanTooltip.appendChild(selectedText);
    range.insertNode(this.spanTooltip);
    this.api.selection.expandToTag(this.spanTooltip);
  }

  unwrap(range: Range) {
    this.spanTooltip = this.api.selection.findParentTag("A");
    if (!this.spanTooltip) return;
    const text = range.extractContents();
    this.spanTooltip.remove();
    range.insertNode(text);
  }

  checkState() {
    this.spanTooltip = this.api.selection.findParentTag("A");
    this.state = !!this.spanTooltip;
    if (this.state) this.showActions();
    else this.hideActions();
    return this.state;
  }

  renderActions() {
    this.spanTooltip = this.api.selection.findParentTag("A");
    this.tooltipInput = document.createElement("input");
    this.tooltipInput.placeholder = "DocLib URL";
    this.tooltipInput.classList.add(this.api.styles.input);
    this.tooltipInput.style.display = "block";
    this.tooltipInput.style.width = "100%";
    this.tooltipInput.style.boxSizing = "border-box";
    this.tooltipInput.style.padding = "5px 10px";
    this.tooltipInput.style.border = "1px solid #e1e1e1";
    this.tooltipInput.style.marginTop = "5px";

    if (this.spanTooltip && this.spanTooltip.getAttribute("href")) {
      this.tooltipInput.value = this.spanTooltip.getAttribute("href")!;
    }
    this.tooltipInput.hidden = true;
    return this.tooltipInput;
  }

  showActions() {
    if (this.tooltipInput) {
      this.tooltipInput.hidden = false;
      setTimeout(() => this.tooltipInput!.focus(), 50);

      this.api.listeners.on(
        this.tooltipInput,
        "keydown",
        (e: any) => {
          if (e.key === "Enter") {
            if (this.spanTooltip) {
              this.spanTooltip.setAttribute("href", this.tooltipInput!.value);
            }
            this.closeToolbar();
          }
        },
        false,
      );
    }
  }

  hideActions() {
    if (this.tooltipInput) this.tooltipInput.hidden = true;
  }

  closeToolbar() {
    const toolbar = document.querySelector(".ce-inline-toolbar--showed");
    if (toolbar) toolbar.classList.remove("ce-inline-toolbar--showed");
  }

  static get sanitize() {
    return {
      a: { href: true, target: true, rel: true, class: true },
    };
  }
}
