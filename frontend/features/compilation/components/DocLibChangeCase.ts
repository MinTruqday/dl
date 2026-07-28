import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibChangeCase implements InlineTool {
  static readonly feature = {
    id: "DocLibChangeCase",
    title: "DocLib ChangeCase",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="446c3f322975e3ea"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="4,10 16,20 11,19 10,17 7,17 20,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;

  static get isInline() {
    return true;
  }
  static get title() {
    return "DocLib Change Case";
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML =
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="446c3f322975e3ea"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="4,10 16,20 11,19 10,17 7,17 20,19"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;

    const selectedText = range.toString();
    if (!selectedText) return;

    let newText = "";

    if (selectedText === selectedText.toUpperCase()) {
      newText = selectedText.toLowerCase();
    } else if (selectedText === selectedText.toLowerCase()) {
      newText = selectedText.replace(
        /\w\S*/g,
        (txt) => txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase(),
      );
    } else {
      newText = selectedText.toUpperCase();
    }

    range.deleteContents();
    range.insertNode(document.createTextNode(newText));

    this.api.selection.expandToTag(document.createElement("span"));
    this.api.inlineToolbar.close();
  }

  checkState() {
    return false;
  }
}
