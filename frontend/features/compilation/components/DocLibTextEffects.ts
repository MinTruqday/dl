import { API } from "@editorjs/editorjs";

export default class DocLibTextEffects {
  static readonly feature = {
    id: "DocLibTextEffects",
    title: "DocLib TextEffects",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a5bf2b8323445c6a"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="16,8 13,16 5,4 11,8 4,18 8,13"/></svg>',
    origin: "doclib-native",
  } as const;

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
    this.button.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a5bf2b8323445c6a"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="16,8 13,16 5,4 11,8 4,18 8,13"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const wrapper = document.createElement("span");
    wrapper.classList.add("doclib-text-effects");
    wrapper.style.textShadow = "1px 1px 2px rgba(15, 23, 42, 0.35)";
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
