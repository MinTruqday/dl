import { API } from "@editorjs/editorjs";

export default class DocLibTextEffects {
  private api: API;
  private button: HTMLElement | null = null;
  private _state: boolean = false;

  static get isInline() {
    return true;
  }

  get state() {
    return this._state;
  }

  set state(state) {
    this._state = state;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, state);
    }
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const wrapper = document.createElement("span");
    wrapper.classList.add("doclib-text-effects");
    wrapper.appendChild(range.extractContents());
    range.insertNode(wrapper);
    this.api.selection.expandToTag(wrapper);
  }

  checkState(selection: Selection) {
    const text = selection.anchorNode;
    if (!text) return;
    const anchorElement = text instanceof Element ? text : text.parentElement;
    if (anchorElement) {
      this.state = !!anchorElement.closest(".doclib-text-effects");
    }
  }
}
