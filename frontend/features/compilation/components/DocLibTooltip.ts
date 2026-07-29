import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibTooltip implements InlineTool {
  static readonly feature = {
    id: "DocLibTooltip",
    title: "Tooltip",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d219c6c081934b8e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,12 15,9 14,15 11,10 12,15 6,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;
  private tooltipInput: HTMLInputElement | null = null;
  private spanTooltip: HTMLElement | null = null;

  static get isInline() {
    return true;
  }
  static get title() {
    return "Tooltip";
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
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="d219c6c081934b8e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,12 15,9 14,15 11,10 12,15 6,4"/></svg>';

    if (!document.getElementById("doclib-tooltip-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-tooltip-styles";
      style.innerHTML = `
            .cdx-tooltip { border-bottom: 1px dashed #388ae5; cursor: help; background-color: rgba(56, 138, 229, 0.1); }
            .tooltip-tool__input { display: block; width: 100%; box-sizing: border-box; padding: 5px 10px; border: 1px solid #e1e1e1; margin-top: 5px; }
        `;
      document.head.appendChild(style);
    }
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
    this.spanTooltip = document.createElement("span");
    this.spanTooltip.classList.add("cdx-tooltip");
    this.spanTooltip.appendChild(selectedText);
    range.insertNode(this.spanTooltip);
    this.api.selection.expandToTag(this.spanTooltip);
  }

  unwrap(range: Range) {
    this.spanTooltip = this.api.selection.findParentTag("SPAN", "cdx-tooltip");
    if (!this.spanTooltip) return;
    const text = range.extractContents();
    this.spanTooltip.remove();
    range.insertNode(text);
  }

  checkState() {
    this.spanTooltip = this.api.selection.findParentTag("SPAN", "cdx-tooltip");
    this.state = !!this.spanTooltip;
    if (this.state) this.showActions();
    else this.hideActions();
    return this.state;
  }

  renderActions() {
    this.spanTooltip = this.api.selection.findParentTag("SPAN", "cdx-tooltip");
    this.tooltipInput = document.createElement("input");
    this.tooltipInput.placeholder = "DocLib Input";
    this.tooltipInput.classList.add(
      this.api.styles.input,
      "tooltip-tool__input",
    );
    if (this.spanTooltip && this.spanTooltip.dataset.tooltip) {
      this.tooltipInput.value = this.spanTooltip.dataset.tooltip;
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
              this.spanTooltip.dataset.tooltip = this.tooltipInput!.value;
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
      span: () => {
        return { class: true, "data-tooltip": true };
      },
    };
  }
}
